from machine import Pin, I2C, freq
from time import *
import random
import ssd1306
import network
import esp32

#Disable Wifi and Bluetooth.
sta = network.WLAN(network.STA_IF)
ap = network.WLAN(network.AP_IF)
sta.active(False)
ap.active(False)
try:
    import bluetooth
    bt = bluetooth.BLE()
    bt.active(False)
except:
    pass

opFreq = 80_000_000
currentFreq = opFreq
idleFreq = 20_000_000

#Screen
i2c = I2C(scl=Pin(9), sda=Pin(8))
oled_width = 128
oled_height = 64
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)

#Action Vars
# 0 = Waiting For Input(Idle)
currentActionID = 0
actionDura = -1
actionMaxDura = 8

def resetDura():
    global actionDura, actionMaxDura
    actionDura = actionMaxDura

#LED Pins
greenLED = Pin(10, Pin.OUT, value = 0)
whiteLED = Pin(4, Pin.OUT, value = 0)
redLED = Pin(20, Pin.OUT, value = 0)
orangeLED = Pin(21, Pin.OUT, value = 0)

scanTime = ticks_ms()
startTime = ticks_ms()
idleTime = ticks_ms()
flashingPin = None
message = None

def notify(ledPin, msg):
    global flashingPin, currentActionID, actionDura, startTime, idleTime
    if actionDura <= 0:
        actionDura = -1
        currentActionID = 0
        flashingPin = None
        message = None
        idleTime = ticks_ms()
        return
        
    oled.text(msg, 0,5)
        
    if ticks_diff(ticks_ms(), startTime) >= 500:
        startTime = ticks_ms()
        ledPin.toggle()
        actionDura -= 1

#Receiver Pins
dataPins = [ Pin(0, Pin.IN, Pin.PULL_UP) ,Pin(1, Pin.IN, Pin.PULL_UP) ,Pin(2, Pin.IN, Pin.PULL_UP) ,Pin(3, Pin.IN, Pin.PULL_UP) ]
dataPinsPrevStats = [ 0, 0, 0, 0 ]

def triggerEvent(pinIndex):
    global flashingPin, currentActionID, actionDura, message
    resetDura()
    if pinIndex == 0:
        flashingPin = whiteLED
        currentActionID = 1
        message = "Clothes Ready!"
        colour = 1
    elif pinIndex == 1:
        flashingPin = greenLED
        currentActionID = 1
        message = "Food Ready!"
        colour = 1
    elif pinIndex == 2:
        flashingPin = redLED
        currentActionID = 1
        message = "Your a dick head!"
        colour = 2
    elif pinIndex == 3:
        flashingPin = orangeLED
        currentActionID = 1
        message = "Come Down!"
        colour = 2
    else:
        actionDura = -1
        print("Invalid Index provided.")

#Checks if the signal is received from receiver then toggle the pins stats alongside prevent repeated presses.
def pinTriggerCheck():
    global opFreq
    index = 0
    while index != len(dataPins):
        dPin = dataPins[index]
        if dataPinsPrevStats[index] != dPin.value():
            if dPin.value() == 1:
                print(f"Pin Activated {index}")
                freq(opFreq)
                dataPinsPrevStats[index] = 1
                triggerEvent(index)
            else:
                dataPinsPrevStats[index] = 0
        index+=1

posX = 0
posY = 16
velX = 1
velY = 1
motds = [
    "Welcome 3rd",
    "Keep calm and debug.",
    "K.I.S.S",
    "Resenfor is a femboy. Confirmed.",
]
currentMOTD = motds[random.randint(0, len(motds) - 1)]
scrollX = len(currentMOTD) * 10


def displayIdle():
    global posX, posY, velX, velY, scrollX, currentMOTD, motds
    oled.text(currentMOTD, scrollX, 0)
    if scrollX + len(currentMOTD) * 10 <= 0:
        currentMOTD = motds[random.randint(0, len(motds) - 1)]
        scrollX = len(currentMOTD) * 10
        
    scrollX -= 1
    oled.drawBoxOutline(posX, posY, 25, 10)
    oled.text("DVD", posX + 1, posY + 2)
    posX += velX
    posY += velY
    if posX <= 0 or posX + 25 >= 128:
        velX *= -1
        posX += velX
    elif posY <= 16 or posY + 10 >= 64:
        velY *= -1
        posY += velY
        
while True:
    oled.fill(0)
    if currentActionID == 0:
        pinTriggerCheck()
        if ticks_diff(ticks_ms(), idleTime) >= 20000:
            displayIdle()
            currentFreq = idleFreq
    elif currentActionID == 1:
        if flashingPin != None and message != None:
            notify(flashingPin, message)
    else:
        currentActionID = 0
    oled.show()
    
    if freq() != currentFreq:
        freq(currentFreq)
        print(f"CPU clock speed set too: {freq()}")

    