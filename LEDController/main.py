from machine import Pin
import neopixel
import network
from time import *
import socket
import _thread
import ujson
import re
import math
from random import *

#Device
global shuttingDown, LEDCOUNT, ledPin, currentPattern, fixedColourDict
shuttingDown = False
print("Starting...")

#Saved Configuration Section
#Modes:
# 0 - Standard LED Controller.
# 1 - Master Controller. (Will send updates and current pattern info to listed slaves.)
# 2 - Slave. (Only does what the set master tell it to do.)
#TODO maybe add a third chain mode where it slave and master to build a chain of controllers.
configData = {
    "mode" : 0,
    "slave_nodes" : [],
    "master_to" : "",
    "default_pattern" : "green_strips",
}

def saveConfig():
    with open("configData.json", "w") as f:
        ujson.dump(configData, f)
    print("Config Data Saved.")

def loadConfig():
    try:
        with open("configData.json", "r") as f:
            configData = ujson.load(f)
        print("Config Data Loaded.")
    except OSError:
        print("Config doesn't exist.")
        saveConfig()
        loadConfig()

#LED Section
def updateState():
    global currentPattern, configData
    if currentPattern == "default":
        currentPattern = configData["default_pattern"]

LEDCOUNT = 300
ledPin = Pin(5, Pin.OUT)
currentPattern = "default"

patternList = [
    "off",
    "default",
    "rainbow",
    "random_strips",
    "black_and_white",
    "red",
    "green",
    "blue",
    "white",
    "dark_green",
    "green_strips"
]

fixedColourDict = {
    "off" : (0, 0, 0),
    "red" : (255, 0, 0),
    "green" : (0, 255, 0),
    "blue" : (0, 0, 255),
    "white" : (255, 255, 255),
    "dark_green" : (0, 100, 0)
}

def hsv_to_rgb_int(h):#AI
    h %= 1536
    segment = h >> 8
    offset  = h & 0xFF 
    if segment == 0:  r, g, b = 255, offset, 0
    elif segment == 1: r, g, b = 255 - offset, 255, 0
    elif segment == 2: r, g, b = 0, 255, offset
    elif segment == 3: r, g, b = 0, 255 - offset, 255
    elif segment == 4: r, g, b = offset, 0, 255
    else:              r, g, b = 255, 0, 255 - offset
    return r, g, b

def ledWorker():
    global shuttingDown, LEDCOUNT, ledPin, currentPattern, neoPix, fixedColourDict
    def applyColour(pix, updateWithLoop, colour = (0,0,0)):
        for i in range(LEDCOUNT):
            pix[i] = colour
            if updateWithLoop:
                pix.write()
        if not updateWithLoop:
            pix.write()
            
    def randomStrips(pix, random=False, colour=(0, 255, 0), blankColour = (0,0,0)):
        cColour = (randint(0, 255), randint(0, 255), randint(0, 255)) if (random) else colour
        counter = 0
        blank = False
        for i in range(LEDCOUNT):
            pix[i] = cColour
            if counter == 0:
                if blank:
                    cColour = blankColour
                    blank = False
                else:
                    cColour = (randint(0, 255), randint(0, 255), randint(0, 255)) if (random) else colour
                    blank = True
                counter = randint(3, 20)
            counter -= 1
            pix.write()
    
    neoPix = neopixel.NeoPixel(ledPin, LEDCOUNT)
    applyColour(neoPix, False)

    sleep(1)
    applyColour(neoPix, False, (255, 255, 255))
    sleep(1)
    
    hue_offset = 0
    hue_step_per_led = 1536 // LEDCOUNT        
        
    while not shuttingDown:
        if currentPattern in fixedColourDict.keys():
            applyColour(neoPix, False, fixedColourDict[currentPattern])
             
        elif currentPattern == "rainbow":
            base = hue_offset
            for i in range(LEDCOUNT):
                rgb = hsv_to_rgb_int(base)
                neoPix[i] = rgb
                base += hue_step_per_led
            neoPix.write()
            hue_offset = (hue_offset + 20) & 0xFFFF
        
        elif currentPattern == "random_strips":
            randomStrips(neoPix, True)
        elif currentPattern == "green_strips":
            randomStrips(neoPix, False, blankColour = (0, 10, 0))
        elif currentPattern == "black_and_white":
            randomStrips(neoPix, False, (255, 255, 255))
        sleep(0.1)
                
#Networking Section
 
netSSID = "AAAAAA"
netPassword = "AAAAAAA"

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

loadConfig()
updateState()

print(f"Socket Started on: {webAddr}")
print("Now Starting LED thread...")
_thread.start_new_thread(ledWorker, ())

try:
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
            
        elif requestURL.count("configstatus") != 0:
            data = {"Message" : "Config Data"}
            data.update(configData)
            replyJson(client, data)
            
        elif requestURL.count("status") != 0:
            data = {"Message" : "My Status", "CurrentPattern" : currentPattern, "IP": webAddr, "WifiName" : netSSID, "LEDCount" : LEDCOUNT }
            replyJson(client, data)
            
        elif requestURL.count("configset") != 0:
            if paramLength <= 0 or paramLength >= 2:
                data = {"Message" : "Error", "Error" : "Too many parameters or no parameters given." }
                replyJson(client, data)
            else:
                param = paramsList[0]
                if param[0] in configData.keys():
                    valueType = type(configData[param[0]])
                    configData[param[0]] = valueType(param[1])
                    data = {"Message" : "Updated Value", f"{param[0]}" : f"{param[1]}" }
                    replyJson(client, data)
                    saveConfig()
                else:
                    data = {"Message" : "Error", "Error" : "The given name doesn't exist?" }
                    replyJson(client, data)
                    
        elif requestURL.count("slavelist") != 0:
            if paramLength <= 0 or paramLength >= 2:
                data = {"Message" : "Error", "Error" : "Too many parameters or no parameters given." }
                replyJson(client, data)
            else:
                param = paramsList[0]
                if param[0] == "add":
                    filterIP = param[1].replace("_", ".")
                    slaveList = configData["slave_nodes"]
                    if filterIP in slaveList:
                        data = {"Message" : "Error", "Error" : "Can't add an already exist node / IP to the list." }
                        replyJson(client, data)
                    else:
                        slaveList.append(filterIP)
                        configData["slave_nodes"] = slaveList
                        saveConfig()
                        data = {"Message" : "Added new Node", "Node IP" : f"{filterIP}" }
                        replyJson(client, data)
                    
                elif param[0] == "remove":
                    filterIP = param[1].replace("_", ".")
                    slaveList = configData["slave_nodes"]
                    if filterIP in slaveList:
                        slaveList.remove(filterIP)
                        configData["slave_nodes"] = slaveList
                        saveConfig()
                        data = {"Message" : "Removed the requested Node", "Node IP" : f"{filterIP}" }
                        replyJson(client, data)
                    else:
                        data = {"Message" : "Error", "Error" : "Can't remove a node / IP thats no in the list." }
                        replyJson(client, data)
                    
                else:
                    data = {"Message" : "Error", "Error" : "Provided command is invalid? Use add to add new nodes or remove to remove a node from the list." }
                    replyJson(client, data)
        
        elif requestURL.count("setmaster") != 0:
            pass
        
        elif requestURL.count("resetconfig") != 0:
            pass
                    
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

except KeyboardInterrupt:
    print("Interrupt detected. Stopping...")
    shuttingDown = True

finally:
    print("Clean up...")
    webSocket.close()
            
print("Bye.")
