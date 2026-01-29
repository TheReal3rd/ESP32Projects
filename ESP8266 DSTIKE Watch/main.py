#WS2812b LED: GPIO 15
from machine import Pin, I2C
from screens.clockFaceScreen import *
import sh1106
import utils

def resyncRTC():
    import network
    station = network.WLAN(network.STA_IF)
    station.active(True)
    station.connect("aaaaa", "aaaa") #TODO move this to a settings file.
    
    if not station.isconnected():
        return

    try:
        #ntptime.settime()
        print("Time synchronized with NTP server.")
    except Exception as e:
        print("Failed to synchronize time:", e)

 
if __name__ == "__main__":
    global currentScreen, i2c
    i2c = I2C(scl=Pin(4),sda=Pin(5), freq=400000)
    utils.init(i2c)
    utils.showClockScreen()
    currentScreen = utils.currentScreen
    
    devices = i2c.scan()
    print(f"I2C Devices: {devices}")

    oled = sh1106.SH1106_I2C(128, 64, i2c, addr=0x3C, rotate=180)

    upButtonPin = Pin(12, Pin.IN, Pin.PULL_UP)
    upButtonPrev = False
    downButtonPin = Pin(13, Pin.IN, Pin.PULL_UP)
    downButtonPrev = False
    selectButtonPin = Pin(14, Pin.IN, Pin.PULL_UP)
    selectButtonPrev = False

    try:
        while True:
            oled.fill(0)
            if currentScreen != utils.currentScreen:
                currentScreen = utils.currentScreen
                
            if currentScreen:
                currentScreen.show(oled)
                
                if currentScreen.isReady():
                    if currentScreen.isButtonLoop():
                        if not upButtonPin.value():
                            currentScreen.upButton()
                        elif not downButtonPin.value():
                            currentScreen.downButton()
                            
                        if not selectButtonPin.value():
                            currentScreen.selectButton()
                    else:
                        if (not upButtonPin.value()) != upButtonPrev:
                            if not upButtonPin.value():
                                currentScreen.upButton()
                                upButtonPrev = True
                            else:
                                upButtonPrev = False
                        
                        if (not downButtonPin.value()) != downButtonPrev:
                            if not downButtonPin.value():
                                currentScreen.downButton()
                                downButtonPrev = True
                            else:
                                downButtonPrev = False
                            
                        if (not selectButtonPin.value()) != selectButtonPrev:
                            if not selectButtonPin.value():
                                currentScreen.selectButton()
                                selectButtonPrev = True
                            else:
                                selectButtonPrev = False
                    
            oled.show()
    except KeyboardInterrupt as er:
        oled.poweroff()
        print("KeyboardInterrupt Detected stopping...")



