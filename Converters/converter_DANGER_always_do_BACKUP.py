fType = 'exr'

import os
import ctypes  # An included library with Python install.

list = os.listdir()
for i in list:
    if i[-3:] == fType:
        os.system("magick convert " + '"' + i + '"' +" "+ '"' + i[:-4]  + ".tif" + '"')

#ctypes.windll.user32.MessageBoxW(0,"Hey, Its DONE!", "Your title", 1)
