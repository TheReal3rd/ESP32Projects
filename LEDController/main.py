from machine import Pin
import neopixel
import network
from time import *
import socket
import _thread
import ujson
import re
import math

#Device
global shuttingDown, LEDCOUNT, ledPin, currentPattern, completed
shuttingDown = False
print("Starting...")

#LED Section
def updateState():
    completed = False

LEDCOUNT = 300
ledPin = Pin(5, Pin.OUT)
currentPattern = "off"
completed = False

patternList = [
    "off",
    "default",
    "rainbow",
    "random_strips",
    "black_and_white",
    "red",
    "green",
    "blue",
]

def hsv_to_rgb_int(h):#AI
    """h = 0..1535 (6 segments × 256) for fast rainbow."""
    h %= 1536  # wrap hue
    
    segment = h >> 8       # 0–5
    offset  = h & 0xFF     # 0–255
    
    if segment == 0:  r, g, b = 255, offset, 0
    elif segment == 1: r, g, b = 255 - offset, 255, 0
    elif segment == 2: r, g, b = 0, 255, offset
    elif segment == 3: r, g, b = 0, 255 - offset, 255
    elif segment == 4: r, g, b = offset, 0, 255
    else:              r, g, b = 255, 0, 255 - offset
    
    return r, g, b

def ledWorker():
    global shuttingDown, LEDCOUNT, ledPin, currentPattern, completed, neoPix
    def applyColour(pix, updateWithLoop, colour = (0,0,0)):
        for i in range(LEDCOUNT):
            pix[i] = colour
            if updateWithLoop:
                pix.write()
        if not updateWithLoop:
            pix.write()
    
    neoPix = neopixel.NeoPixel(ledPin, LEDCOUNT)
    applyColour(neoPix, False)

    sleep(1)
    applyColour(neoPix, False, (255, 255, 255))
    sleep(1)
    
    hue_offset = 0
    hue_step_per_led = 1536 // LEDCOUNT
    
    while not shuttingDown:
        if currentPattern == "off":
            if not completed:
                applyColour(neoPix, False)
                completed = True
                
        elif currentPattern == "rainbow":
            base = hue_offset
            for i in range(LEDCOUNT):
                rgb = hsv_to_rgb_int(base)
                neoPix[i] = rgb
                base += hue_step_per_led
            neoPix.write()

            hue_offset = (hue_offset + 20) & 0xFFFF
            #sleep(0.001)

#Networking Section
netSSID = "AAAA"
netPassword = "AAAAA"

#Networking handling:
netWlan = network.WLAN(network.STA_IF)
netWlan.active(True)
netWlan.connect(netSSID, netPassword)

deviceIP = None

netTries = 10
while netTries != 0:
    if netWlan.status() < 0 or netWlan.status() >= 3:
        print("Connection Successful...")
        break
    netTries -= 1
    print("Failed to connect retrying...")
    time.sleep(1)
    
netInfo = netWlan.ifconfig()
deviceIP = netInfo[0]
    
print(f"Device IP: {deviceIP}")
    
#Web Socket API handling
def replyJson(client, data):
    client.send('HTTP/1.1 200 OK\r\n')
    client.send('Content-Type: text/json\r\n')
    client.send('Connection: close\r\n\r\n')
    client.sendall(ujson.dumps(data).encode())
    client.close()
    
def sCleanup(stringContent):
    return re.sub(r'[^A-Za-z0-9_]', '', stringContent)

webAddr = (deviceIP, 80)
webSocket = socket.socket()
webSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
webSocket.bind(webAddr)
webSocket.listen(1)
    
print(f"Socket Started on: {webAddr}")
print("Now Starting LED thread...")
_thread.start_new_thread(ledWorker, ())

while not shuttingDown:
    client, clientAddr = webSocket.accept()
    rawRequest = client.recv(1024)
    requestParts = rawRequest.split()
    httpMethods = requestParts[0]
    requestURL = str(requestParts[1]).replace("/", "").lower()
    paramsList = []
    paramLength = 0
    if requestURL.count("?") != 0:
        paramSplit = requestURL.split("?")
        requestURL = paramSplit[0]
        for param in paramSplit[1].split("&"):
            valueSplit = param.split("=")
            paramsList.append( ( sCleanup(str(valueSplit[0].lower())), sCleanup(str(valueSplit[1].lower()))) )
        paramLength = len(paramsList)
  
    print(f"URL: {requestURL} Params: {paramsList}")
    if requestURL.count("ledon") != 0:
        currentPattern = "default"
        updateState()
        data = {"Message" : "Started...", "CurrentPattern" : currentPattern }
        replyJson(client, data)
        
    elif requestURL.count("ledoff") != 0:
        currentPattern = "off"
        updateState()
        data = {"Message" : "Started...", "CurrentPattern" : currentPattern }
        replyJson(client, data)
        
    elif requestURL.count("status") != 0:
        data = {"Message" : "My Status", "CurrentPattern" : currentPattern, "IP": webAddr, "WifiName" : netSSID, "LEDCount" : LEDCOUNT }
        replyJson(client, data)
        
    elif requestURL.count("mode") != 0:
        if paramLength <= 0 or paramLength >= 2:
            data = {"Message" : "Error", "Error" : "Too many parameters or no parameters given." }
            replyJson(client, data)
        else:
            param = paramsList[0]
            if param[0] == "pattern":
                if param[1] in patternList:
                    currentPattern = param[1]
                    updateState()
                    data = {"Message" : "Updated Mode", "CurrentPattern" : currentPattern }
                    replyJson(client, data)
                else:
                    data = {"Message" : "Error", "Error" : "Provided pattern isn't within the list?" }
                    replyJson(client, data)
            else:
                data = {"Message" : "Failed", "Error" : "Provided data name abnormally or incorrectly provided Ensure naming is correct." }
                replyJson(client, data)
                
        
    elif requestURL.count("shutdown") != 0:
        print("Shutting down.")
        webSocket.close()
        shuttingDown = True
        continue
        
        
print("Bye.")


    

