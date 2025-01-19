# displayio introduction
GUI written in MicroPython。  
now widget only support label and button, and device only support st7789  
but it is easy to extern other driver and widget

The usage is  same as [Beeware Toga](https://github.com/beeware/toga.git) .  
And it is CSS like too.  

Now, it provides for container box (flex, free, grid and scroll).    

Input device support esp32 TouchPad, physical button and encoder. input device provide a useful func to en able you map a default event output to any other event.  

the display is dynamical, so show_fps is not correct.
you can specify the fps in init of display.

# create your own widget
1. you need to import the base widget file  
   `import displayio.widget.widget`
2. rewrite the func called `widget.draw`, you can find the example in label.py or button.py
3. the `widget.draw` is aim to draw `widget._bitmap` and wait for render system to blit it to screen or gloable `root._bitmap`

