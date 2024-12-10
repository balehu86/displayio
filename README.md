# displayio
GUI written in MicroPython。  
now widget only support label  
device only support st7789

the usage is really same as [Beeware Toga](https://github.com/beeware/toga.git) .  
and it is same as CSS too.  

now, it provides two box (flex and free). the grid box is not finish.  

input device only support esp32 TouchPad, because i donot have a physical button.  

you can write a virtual input device in main() function and push it to display.run().
it will run at every loop.

the display is dynamical, so show_fps is not correct.
you can specify the fps in init of display.


