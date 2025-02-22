/*
 * This file is part of the MicroPython project, http://micropython.org/
 *
 * The MIT License (MIT)
 *
 * Copyright (c) 2016 Damien P. George
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */

#include <stdio.h>
#include <string.h>

#include "py/runtime.h"
#include "py/binary.h"



typedef struct _mp_obj_framebuf_t {
    mp_obj_base_t base;
    mp_obj_t buf_obj; // need to store this to prevent GC from reclaiming buf
    void *buf;
    uint16_t width, height, stride;
    uint8_t format;
} mp_obj_framebuf_t;

#if !MICROPY_ENABLE_DYNRUNTIME
static const mp_obj_type_t mp_type_framebuf;
#endif

typedef void (*setpixel_t)(const mp_obj_framebuf_t *, unsigned int, unsigned int, uint32_t);
typedef uint32_t (*getpixel_t)(const mp_obj_framebuf_t *, unsigned int, unsigned int);
typedef void (*fill_rect_t)(const mp_obj_framebuf_t *, unsigned int, unsigned int, unsigned int, unsigned int, uint32_t);

typedef struct _mp_framebuf_p_t {
    setpixel_t setpixel;
    getpixel_t getpixel;
    fill_rect_t fill_rect;
} mp_framebuf_p_t;

// constants for formats
#define FRAMEBUF_MVLSB    (0)
#define FRAMEBUF_RGB565   (1)
#define FRAMEBUF_GS2_HMSB (5)
#define FRAMEBUF_GS4_HMSB (2)
#define FRAMEBUF_GS8      (6)
#define FRAMEBUF_MHLSB    (3)
#define FRAMEBUF_MHMSB    (4)

// Functions for MHLSB and MHMSB

static void mono_horiz_setpixel(const mp_obj_framebuf_t *fb, unsigned int x, unsigned int y, uint32_t col) {
    size_t index = (x + y * fb->stride) >> 3;
    unsigned int offset = fb->format == FRAMEBUF_MHMSB ? x & 0x07 : 7 - (x & 0x07);
    ((uint8_t *)fb->buf)[index] = (((uint8_t *)fb->buf)[index] & ~(0x01 << offset)) | ((col != 0) << offset);
}

static uint32_t mono_horiz_getpixel(const mp_obj_framebuf_t *fb, unsigned int x, unsigned int y) {
    size_t index = (x + y * fb->stride) >> 3;
    unsigned int offset = fb->format == FRAMEBUF_MHMSB ? x & 0x07 : 7 - (x & 0x07);
    return (((uint8_t *)fb->buf)[index] >> (offset)) & 0x01;
}

static void mono_horiz_fill_rect(const mp_obj_framebuf_t *fb, unsigned int x, unsigned int y, unsigned int w, unsigned int h, uint32_t col) {
    unsigned int reverse = fb->format == FRAMEBUF_MHMSB;
    unsigned int advance = fb->stride >> 3;
    while (w--) {
        uint8_t *b = &((uint8_t *)fb->buf)[(x >> 3) + y * advance];
        unsigned int offset = reverse ?  x & 7 : 7 - (x & 7);
        for (unsigned int hh = h; hh; --hh) {
            *b = (*b & ~(0x01 << offset)) | ((col != 0) << offset);
            b += advance;
        }
        ++x;
    }
}

// Functions for MVLSB format

static void mvlsb_setpixel(const mp_obj_framebuf_t *fb, unsigned int x, unsigned int y, uint32_t col) {
    size_t index = (y >> 3) * fb->stride + x;
    uint8_t offset = y & 0x07;
    ((uint8_t *)fb->buf)[index] = (((uint8_t *)fb->buf)[index] & ~(0x01 << offset)) | ((col != 0) << offset);
}

static uint32_t mvlsb_getpixel(const mp_obj_framebuf_t *fb, unsigned int x, unsigned int y) {
    return (((uint8_t *)fb->buf)[(y >> 3) * fb->stride + x] >> (y & 0x07)) & 0x01;
}

static void mvlsb_fill_rect(const mp_obj_framebuf_t *fb, unsigned int x, unsigned int y, unsigned int w, unsigned int h, uint32_t col) {
    while (h--) {
        uint8_t *b = &((uint8_t *)fb->buf)[(y >> 3) * fb->stride + x];
        uint8_t offset = y & 0x07;
        for (unsigned int ww = w; ww; --ww) {
            *b = (*b & ~(0x01 << offset)) | ((col != 0) << offset);
            ++b;
        }
        ++y;
    }
}

// Functions for RGB565 format

static void rgb565_setpixel(const mp_obj_framebuf_t *fb, unsigned int x, unsigned int y, uint32_t col) {
    ((uint16_t *)fb->buf)[x + y * fb->stride] = col;
}

static uint32_t rgb565_getpixel(const mp_obj_framebuf_t *fb, unsigned int x, unsigned int y) {
    return ((uint16_t *)fb->buf)[x + y * fb->stride];
}

static void rgb565_fill_rect(const mp_obj_framebuf_t *fb, unsigned int x, unsigned int y, unsigned int w, unsigned int h, uint32_t col) {
    uint16_t *b = &((uint16_t *)fb->buf)[x + y * fb->stride];
    while (h--) {
        for (unsigned int ww = w; ww; --ww) {
            *b++ = col;
        }
        b += fb->stride - w;
    }
}

// Functions for GS2_HMSB format

static void gs2_hmsb_setpixel(const mp_obj_framebuf_t *fb, unsigned int x, unsigned int y, uint32_t col) {
    uint8_t *pixel = &((uint8_t *)fb->buf)[(x + y * fb->stride) >> 2];
    uint8_t shift = (x & 0x3) << 1;
    uint8_t mask = 0x3 << shift;
    uint8_t color = (col & 0x3) << shift;
    *pixel = color | (*pixel & (~mask));
}

static uint32_t gs2_hmsb_getpixel(const mp_obj_framebuf_t *fb, unsigned int x, unsigned int y) {
    uint8_t pixel = ((uint8_t *)fb->buf)[(x + y * fb->stride) >> 2];
    uint8_t shift = (x & 0x3) << 1;
    return (pixel >> shift) & 0x3;
}

static void gs2_hmsb_fill_rect(const mp_obj_framebuf_t *fb, unsigned int x, unsigned int y, unsigned int w, unsigned int h, uint32_t col) {
    for (unsigned int xx = x; xx < x + w; xx++) {
        for (unsigned int yy = y; yy < y + h; yy++) {
            gs2_hmsb_setpixel(fb, xx, yy, col);
        }
    }
}

// Functions for GS4_HMSB format

static void gs4_hmsb_setpixel(const mp_obj_framebuf_t *fb, unsigned int x, unsigned int y, uint32_t col) {
    uint8_t *pixel = &((uint8_t *)fb->buf)[(x + y * fb->stride) >> 1];

    if (x % 2) {
        *pixel = ((uint8_t)col & 0x0f) | (*pixel & 0xf0);
    } else {
        *pixel = ((uint8_t)col << 4) | (*pixel & 0x0f);
    }
}

static uint32_t gs4_hmsb_getpixel(const mp_obj_framebuf_t *fb, unsigned int x, unsigned int y) {
    if (x % 2) {
        return ((uint8_t *)fb->buf)[(x + y * fb->stride) >> 1] & 0x0f;
    }

    return ((uint8_t *)fb->buf)[(x + y * fb->stride) >> 1] >> 4;
}

static void gs4_hmsb_fill_rect(const mp_obj_framebuf_t *fb, unsigned int x, unsigned int y, unsigned int w, unsigned int h, uint32_t col) {
    col &= 0x0f;
    uint8_t *pixel_pair = &((uint8_t *)fb->buf)[(x + y * fb->stride) >> 1];
    uint8_t col_shifted_left = col << 4;
    uint8_t col_pixel_pair = col_shifted_left | col;
    unsigned int pixel_count_till_next_line = (fb->stride - w) >> 1;
    bool odd_x = (x % 2 == 1);

    while (h--) {
        unsigned int ww = w;

        if (odd_x && ww > 0) {
            *pixel_pair = (*pixel_pair & 0xf0) | col;
            pixel_pair++;
            ww--;
        }

        memset(pixel_pair, col_pixel_pair, ww >> 1);
        pixel_pair += ww >> 1;

        if (ww % 2) {
            *pixel_pair = col_shifted_left | (*pixel_pair & 0x0f);
            if (!odd_x) {
                pixel_pair++;
            }
        }

        pixel_pair += pixel_count_till_next_line;
    }
}

// Functions for GS8 format

static void gs8_setpixel(const mp_obj_framebuf_t *fb, unsigned int x, unsigned int y, uint32_t col) {
    uint8_t *pixel = &((uint8_t *)fb->buf)[(x + y * fb->stride)];
    *pixel = col & 0xff;
}

static uint32_t gs8_getpixel(const mp_obj_framebuf_t *fb, unsigned int x, unsigned int y) {
    return ((uint8_t *)fb->buf)[(x + y * fb->stride)];
}

static void gs8_fill_rect(const mp_obj_framebuf_t *fb, unsigned int x, unsigned int y, unsigned int w, unsigned int h, uint32_t col) {
    uint8_t *pixel = &((uint8_t *)fb->buf)[(x + y * fb->stride)];
    while (h--) {
        memset(pixel, col, w);
        pixel += fb->stride;
    }
}

static mp_framebuf_p_t formats[] = {
    [FRAMEBUF_MVLSB] = {mvlsb_setpixel, mvlsb_getpixel, mvlsb_fill_rect},
    [FRAMEBUF_RGB565] = {rgb565_setpixel, rgb565_getpixel, rgb565_fill_rect},
    [FRAMEBUF_GS2_HMSB] = {gs2_hmsb_setpixel, gs2_hmsb_getpixel, gs2_hmsb_fill_rect},
    [FRAMEBUF_GS4_HMSB] = {gs4_hmsb_setpixel, gs4_hmsb_getpixel, gs4_hmsb_fill_rect},
    [FRAMEBUF_GS8] = {gs8_setpixel, gs8_getpixel, gs8_fill_rect},
    [FRAMEBUF_MHLSB] = {mono_horiz_setpixel, mono_horiz_getpixel, mono_horiz_fill_rect},
    [FRAMEBUF_MHMSB] = {mono_horiz_setpixel, mono_horiz_getpixel, mono_horiz_fill_rect},
};

static inline void setpixel(const mp_obj_framebuf_t *fb, unsigned int x, unsigned int y, uint32_t col) {
    formats[fb->format].setpixel(fb, x, y, col);
}

static void setpixel_checked(const mp_obj_framebuf_t *fb, mp_int_t x, mp_int_t y, mp_int_t col, mp_int_t mask) {
    if (mask && 0 <= x && x < fb->width && 0 <= y && y < fb->height) {
        setpixel(fb, x, y, col);
    }
}

static inline uint32_t getpixel(const mp_obj_framebuf_t *fb, unsigned int x, unsigned int y) {
    return formats[fb->format].getpixel(fb, x, y);
}

static void fill_rect(const mp_obj_framebuf_t *fb, int x, int y, int w, int h, uint32_t col) {
    if (h < 1 || w < 1 || x + w <= 0 || y + h <= 0 || y >= fb->height || x >= fb->width) {
        // No operation needed.
        return;
    }

    // clip to the framebuffer
    int xend = MIN(fb->width, x + w);
    int yend = MIN(fb->height, y + h);
    x = MAX(x, 0);
    y = MAX(y, 0);

    formats[fb->format].fill_rect(fb, x, y, xend - x, yend - y, col);
}

static mp_obj_t framebuf_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *args_in) {
    mp_arg_check_num(n_args, n_kw, 4, 5, false);

    mp_int_t width = mp_obj_get_int(args_in[1]);
    mp_int_t height = mp_obj_get_int(args_in[2]);
    mp_int_t format = mp_obj_get_int(args_in[3]);
    mp_int_t stride = n_args >= 5 ? mp_obj_get_int(args_in[4]) : width;

    if (width < 1 || height < 1 || width > 0xffff || height > 0xffff || stride > 0xffff || stride < width) {
        mp_raise_ValueError(NULL);
    }

    size_t bpp = 1;
    size_t height_required = height;
    size_t width_required = width;
    size_t strides_required = height - 1;

    switch (format) {
        case FRAMEBUF_MVLSB:
            height_required = (height + 7) & ~7;
            strides_required = height_required - 8;
            break;
        case FRAMEBUF_MHLSB:
        case FRAMEBUF_MHMSB:
            stride = (stride + 7) & ~7;
            width_required = (width + 7) & ~7;
            break;
        case FRAMEBUF_GS2_HMSB:
            stride = (stride + 3) & ~3;
            width_required = (width + 3) & ~3;
            bpp = 2;
            break;
        case FRAMEBUF_GS4_HMSB:
            stride = (stride + 1) & ~1;
            width_required = (width + 1) & ~1;
            bpp = 4;
            break;
        case FRAMEBUF_GS8:
            bpp = 8;
            break;
        case FRAMEBUF_RGB565:
            bpp = 16;
            break;
        default:
            mp_raise_ValueError(MP_ERROR_TEXT("invalid format"));
    }

    mp_buffer_info_t bufinfo;
    mp_get_buffer_raise(args_in[0], &bufinfo, MP_BUFFER_WRITE);

    if ((strides_required * stride + (height_required - strides_required) * width_required) * bpp / 8 > bufinfo.len) {
        mp_raise_ValueError(NULL);
    }

    mp_obj_framebuf_t *o = mp_obj_malloc(mp_obj_framebuf_t, type);
    o->buf_obj = args_in[0];
    o->buf = bufinfo.buf;
    o->width = width;
    o->height = height;
    o->format = format;
    o->stride = stride;

    return MP_OBJ_FROM_PTR(o);
}

static void framebuf_args(const mp_obj_t *args_in, mp_int_t *args_out, int n) {
    for (int i = 0; i < n; ++i) {
        args_out[i] = mp_obj_get_int(args_in[i + 1]);
    }
}

static mp_int_t framebuf_get_buffer(mp_obj_t self_in, mp_buffer_info_t *bufinfo, mp_uint_t flags) {
    mp_obj_framebuf_t *self = MP_OBJ_TO_PTR(self_in);
    return mp_get_buffer(self->buf_obj, bufinfo, flags) ? 0 : 1;
}

static mp_obj_t framebuf_fill(mp_obj_t self_in, mp_obj_t col_in) {
    mp_obj_framebuf_t *self = MP_OBJ_TO_PTR(self_in);
    mp_int_t col = mp_obj_get_int(col_in);
    formats[self->format].fill_rect(self, 0, 0, self->width, self->height, col);
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_2(framebuf_fill_obj, framebuf_fill);

static mp_obj_t framebuf_fill_rect(size_t n_args, const mp_obj_t *args_in) {
    mp_obj_framebuf_t *self = MP_OBJ_TO_PTR(args_in[0]);
    mp_int_t args[5]; // x, y, w, h, col
    framebuf_args(args_in, args, 5);
    fill_rect(self, args[0], args[1], args[2], args[3], args[4]);
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(framebuf_fill_rect_obj, 6, 6, framebuf_fill_rect);

static mp_obj_t framebuf_pixel(size_t n_args, const mp_obj_t *args_in) {
    mp_obj_framebuf_t *self = MP_OBJ_TO_PTR(args_in[0]);
    mp_int_t x = mp_obj_get_int(args_in[1]);
    mp_int_t y = mp_obj_get_int(args_in[2]);
    if (0 <= x && x < self->width && 0 <= y && y < self->height) {
        if (n_args == 3) {
            // get
            return MP_OBJ_NEW_SMALL_INT(getpixel(self, x, y));
        } else {
            // set
            setpixel(self, x, y, mp_obj_get_int(args_in[3]));
        }
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(framebuf_pixel_obj, 3, 4, framebuf_pixel);

static mp_obj_t framebuf_blit(size_t n_args, const mp_obj_t *args_in) {
    mp_obj_framebuf_t *self = MP_OBJ_TO_PTR(args_in[0]);
    mp_obj_t source_in = mp_obj_cast_to_native_base(args_in[1], MP_OBJ_FROM_PTR(&mp_type_framebuf));
    if (source_in == MP_OBJ_NULL) {
        mp_raise_TypeError(NULL);
    }
    mp_obj_framebuf_t *source = MP_OBJ_TO_PTR(source_in);

    mp_int_t x = mp_obj_get_int(args_in[2]);
    mp_int_t y = mp_obj_get_int(args_in[3]);
    mp_int_t key = -1;
    if (n_args > 4) {
        key = mp_obj_get_int(args_in[4]);
    }
    mp_obj_framebuf_t *palette = NULL;
    if (n_args > 5 && args_in[5] != mp_const_none) {
        palette = MP_OBJ_TO_PTR(mp_obj_cast_to_native_base(args_in[5], MP_OBJ_FROM_PTR(&mp_type_framebuf)));
    }

    if (
        (x >= self->width) ||
        (y >= self->height) ||
        (-x >= source->width) ||
        (-y >= source->height)
        ) {
        // Out of bounds, no-op.
        return mp_const_none;
    }

    // Clip.
    int x0 = MAX(0, x);
    int y0 = MAX(0, y);
    int x1 = MAX(0, -x);
    int y1 = MAX(0, -y);
    int x0end = MIN(self->width, x + source->width);
    int y0end = MIN(self->height, y + source->height);

    for (; y0 < y0end; ++y0) {
        int cx1 = x1;
        for (int cx0 = x0; cx0 < x0end; ++cx0) {
            uint32_t col = getpixel(source, cx1, y1);
            if (palette) {
                col = getpixel(palette, col, 0);
            }
            if (col != (uint32_t)key) {
                setpixel(self, cx0, y0, col);
            }
            ++cx1;
        }
        ++y1;
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(framebuf_blit_obj, 4, 6, framebuf_blit);

static mp_obj_t framebuf_scroll(mp_obj_t self_in, mp_obj_t xstep_in, mp_obj_t ystep_in) {
    mp_obj_framebuf_t *self = MP_OBJ_TO_PTR(self_in);
    mp_int_t xstep = mp_obj_get_int(xstep_in);
    mp_int_t ystep = mp_obj_get_int(ystep_in);
    int sx, y, xend, yend, dx, dy;
    if (xstep < 0) {
        sx = 0;
        xend = self->width + xstep;
        if (xend <= 0) {
            return mp_const_none;
        }
        dx = 1;
    } else {
        sx = self->width - 1;
        xend = xstep - 1;
        if (xend >= sx) {
            return mp_const_none;
        }
        dx = -1;
    }
    if (ystep < 0) {
        y = 0;
        yend = self->height + ystep;
        if (yend <= 0) {
            return mp_const_none;
        }
        dy = 1;
    } else {
        y = self->height - 1;
        yend = ystep - 1;
        if (yend >= y) {
            return mp_const_none;
        }
        dy = -1;
    }
    for (; y != yend; y += dy) {
        for (int x = sx; x != xend; x += dx) {
            setpixel(self, x, y, getpixel(self, x - xstep, y - ystep));
        }
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_3(framebuf_scroll_obj, framebuf_scroll);

#if !MICROPY_ENABLE_DYNRUNTIME
static const mp_rom_map_elem_t framebuf_locals_dict_table[] = {
    { MP_ROM_QSTR(MP_QSTR_fill), MP_ROM_PTR(&framebuf_fill_obj) },
    { MP_ROM_QSTR(MP_QSTR_fill_rect), MP_ROM_PTR(&framebuf_fill_rect_obj) },
    { MP_ROM_QSTR(MP_QSTR_pixel), MP_ROM_PTR(&framebuf_pixel_obj) },
    { MP_ROM_QSTR(MP_QSTR_blit), MP_ROM_PTR(&framebuf_blit_obj) },
    { MP_ROM_QSTR(MP_QSTR_scroll), MP_ROM_PTR(&framebuf_scroll_obj) },
};
static MP_DEFINE_CONST_DICT(framebuf_locals_dict, framebuf_locals_dict_table);

static MP_DEFINE_CONST_OBJ_TYPE(
    mp_type_framebuf,
    MP_QSTR_FrameBuffer,
    MP_TYPE_FLAG_NONE,
    make_new, framebuf_make_new,
    buffer, framebuf_get_buffer,
    locals_dict, &framebuf_locals_dict
    );
#endif

#if !MICROPY_ENABLE_DYNRUNTIME
// This factory function is provided for backwards compatibility with the old
static const mp_rom_map_elem_t framebuf_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_framebuf) },
    { MP_ROM_QSTR(MP_QSTR_FrameBuffer), MP_ROM_PTR(&mp_type_framebuf) },
    { MP_ROM_QSTR(MP_QSTR_MVLSB), MP_ROM_INT(FRAMEBUF_MVLSB) },
    { MP_ROM_QSTR(MP_QSTR_MONO_VLSB), MP_ROM_INT(FRAMEBUF_MVLSB) },
    { MP_ROM_QSTR(MP_QSTR_RGB565), MP_ROM_INT(FRAMEBUF_RGB565) },
    { MP_ROM_QSTR(MP_QSTR_GS2_HMSB), MP_ROM_INT(FRAMEBUF_GS2_HMSB) },
    { MP_ROM_QSTR(MP_QSTR_GS4_HMSB), MP_ROM_INT(FRAMEBUF_GS4_HMSB) },
    { MP_ROM_QSTR(MP_QSTR_GS8), MP_ROM_INT(FRAMEBUF_GS8) },
    { MP_ROM_QSTR(MP_QSTR_MONO_HLSB), MP_ROM_INT(FRAMEBUF_MHLSB) },
    { MP_ROM_QSTR(MP_QSTR_MONO_HMSB), MP_ROM_INT(FRAMEBUF_MHMSB) },
};

static MP_DEFINE_CONST_DICT(framebuf_module_globals, framebuf_module_globals_table);

const mp_obj_module_t mp_module_framebuf = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&framebuf_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_framebuf, mp_module_framebuf);
#endif
