import urandom
from screens.selectMenuScreen import *
from screens.dvdScreen import *
from screens.pongScreen import *
from screens.clockFaceScreen import *

currentScreen = None
_i2c = None

def init(i2c):
    global _i2c
    _i2c = i2c

def showDVDScreen():
    global currentScreen
    currentScreen = dvdScreen()
    
def showPongScreen():
    global currentScreen
    currentScreen = pongScreen()
    
def showClockScreen():
    global currentScreen
    currentScreen = clockFaceScreen(_i2c)
    
def showSelectScreen():
    global currentScreen
    currentScreen = selectMenuScreen(startMenu)

startMenu = {
    "DVD" : showDVDScreen,
    "Pong" : showPongScreen,
    "Clock" : showClockScreen,
    "test4" : None
}

#AI Limited Random library support for ESP8266
def randint(min_val, max_val):
    span = max_val - min_val + 1
    div = 0x3fffffff // span
    offset = urandom.getrandbits(30) // div
    return min_val + offset

def clamp(value, minValue, maxValue):
    return min(maxValue, max(value, minValue))



