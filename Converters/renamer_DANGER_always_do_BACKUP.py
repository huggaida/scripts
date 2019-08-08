fType = 'cxr'

import os
import ctypes  # An included library with Python install.

list = os.listdir()
for i in list:
    if i[-3:] == fType:
        os.system("move " + '"' +i + '"' +" "+ '"' + i[:-4]  + ".exr" + '"')
        print("move " + '"' +i + '"' +" "+ '"' + i[:-4]  + ".exr" + '"')

#ctypes.windll.user32.MessageBoxW(0,"Hey, Its DONE!", "Your title", 1)
