"""This example is for Raspberry Pi (Linux) only!
   It will not work on microcontrollers running CircuitPython!"""

import os
import math
import time, datetime

import busio
import board

import numpy as np
import pygame
from scipy.interpolate import griddata

from colour import Color

import adafruit_amg88xx

i2c_bus = busio.I2C(board.SCL, board.SDA)

#low range of the sensor (this will be blue on the screen)
MINTEMP = 26.

#high range of the sensor (this will be red on the screen)
MAXTEMP = 32.

#how many color values we can have
COLORDEPTH = 1024

# FULL SCREEN COLORS
WHITE = (255,255,255)
BLACK = (0,0,0)
BLUE  = (0,0,255)
YELLOW= (255,255,0)
CYAN  = (0,255,255)
RED   = (255,0,0)
GRAY  = (128,128,128)


os.putenv('SDL_FBDEV', '/dev/fb1')
pygame.init()

#initialize the sensor
sensor = adafruit_amg88xx.AMG88XX(i2c_bus, addr=0x68)

# pylint: disable=invalid-slice-index
points = [(math.floor(ix / 8), (ix % 8)) for ix in range(0, 64)]
grid_x, grid_y = np.mgrid[0:7:32j, 0:7:32j]
# pylint: enable=invalid-slice-index

#sensor is an 8x8 grid so lets do a square
height = 240
width = 240

#the list of colors we can choose from
blue = Color("indigo")
colors = list(blue.range_to(Color("red"), COLORDEPTH))

#create the array of colors
colors = [(int(c.red * 255), int(c.green * 255), int(c.blue * 255)) for c in colors]

displayPixelWidth = width / 30
displayPixelHeight = height / 30

lcd = pygame.display.set_mode((width, height))

lcd.fill((255, 0, 0))

pygame.display.update()
pygame.mouse.set_visible(False)

lcd.fill((0, 0, 0))
pygame.display.update()

#some utility functions
def constrain(val, min_val, max_val):
    return min(max_val, max(min_val, val))

def map_value(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

#let the sensor initialize
time.sleep(.1)
showBtns = 0
offset = 0
loop = 1

while True:

    #read the pixels

    pixels = []
    pixels_d = sensor.pixels

    for row in pixels_d:
        # Pad to 1 decimal place
        print(['{0:.1f}'.format(temp) for temp in row])
        print("")
    print("\n")
    time.sleep(1)

    max_temp = max(pixels_d)
    min_temp = min(pixels_d)
#    print("Max = {0:.1f} C".format(max_index))
    print("Max Temp = ", max(max_temp))
    print("Min Temp = ", min(min_temp))

#    for row in sensor.pixels:
    for row in pixels_d:
        pixels = pixels + row
    pixels = [map_value(p, MINTEMP, MAXTEMP, 0, COLORDEPTH - 1) for p in pixels]

    #perform interpolation
    bicubic = griddata(points, pixels, (grid_x, grid_y), method='cubic')

    #draw everything
    for ix, row in enumerate(bicubic):
        for jx, pixel in enumerate(row):
            pygame.draw.rect(lcd, colors[constrain(int(pixel), 0, COLORDEPTH- 1)],
                             (displayPixelHeight * ix, displayPixelWidth * jx,
                              displayPixelHeight, displayPixelWidth))

    # Flip the screen horizontally to match front facing IP camera
    surf = pygame.transform.flip(lcd,True,False)
    lcd.blit(surf,(0,0))

    fnt = pygame.font.Font(None, 15)
    mode_buttons = {'PWR ->':(280,40), '   UP ->':(280,100), 'DOWN->':(280,160), 'MODE->':(280,220)}
    for k,v in mode_buttons.items():
        text_surface = fnt.render('%s'%k, True, GRAY)
        rect = text_surface.get_rect(center=v)
        lcd.blit(text_surface, rect)
        showBtns = showBtns + 1
        # Add Data to screen
        fnt = pygame.font.Font(None, 15)
        cur_date = datetime.datetime.now().strftime('%a  %d  %b %H : %M : %S %Z %Y') 
        text_surface = fnt.render(cur_date, True, GRAY)
        fnt = pygame.font.Font(None, 35)
        lcd.blit(text_surface, (10,220))
        text = "Min  = {0:.1f} C".format(min(min_temp))
        text_surface = fnt.render(text, True, GRAY)
        lcd.blit(text_surface, (10,20))
        text = "Max = {0:.1f} C".format(max(max_temp))
        text_surface = fnt.render(text, True, GRAY)
        lcd.blit(text_surface, (10,40))


    pygame.display.update()


