from machine import Pin, reset
from gc import collect, mem_free
from random import randint, choice
from time import sleep, time

import neopixel
import network
import socket
import _thread

#Device
global shuttingDown, LEDCOUNT, ledPin, currentPattern, fixedColourDict, configData, GITURL, VERSION, pongDirection, pongPos, pongWidth
shuttingDown = False
print("Starting...")
#Software information
VERSION = "1.4"
CREDITS = "TheReal3rd"
GITURL = "http://51.158.144.14/files/ledController/{fileName}"
FILES_DICT = {
    "ver" : "version.json",
    "controller" : "controller.py"
}

#Self Updating Section
def checkForUpdates(forceDownload=False):
    import urequests
    import ujson
    global GITURL
    doUpdate = False
    try:
        url = GITURL.format(fileName = FILES_DICT["ver"])
        print(url)
        response = urequests.get(url)
        
        if response.status_code == 200:
            print("Successfully fetch update information.")
            responseDict = ujson.loads(response.text)
            
            if responseDict["Version"] != VERSION:
                print("Update is needed.")
                if configData["auto_update"]:
                    doUpdate = True
            else:
                print("No updates are needed.")
        else:
            print("Failed to fetch update information.")
                
        response.close()
    except Exception as e:
        print(f"Check Update Request failed: {e}")
        
    if doUpdate or forceDownload:
        downloadUpdates()

def downloadUpdates():
    import urequests
    print("Started Updates creating backup now...")
    backupCode = None
    with open("controller.py", "r") as f:
        backupCode = f.read()
    
    if backupCode:
        with open("controller.py.bak", "w") as f:
            f.write(backupCode)
    
    sleep(0.5)
    print("Freeing up memory.")
    collect()
    print(f"Currently avaible memory: {mem_free()}")
    sleep(0.5)
    
    print("Starting download.")
    try:
        url = GITURL.format(fileName = FILES_DICT["controller"])
        print(url)
        response = urequests.get(url)
        
        print(response.status_code)
        
        if response.status_code == 200:
            print("Downloaded update...")
            with open("controller.py", "w") as f:
                f.write(response.text)
                
            print("Finished update process. Restarting...")
            reset()
        else:
            print("Failed to fetch update information.")
                
        response.close()
    except Exception as e:
        print(f"Update download request failed: {e}")
        
    

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
    "on_boot_distribute" : True,
    "auto_update" : True,
    "auto_update_check" : True,
    "net_ssid" : "",
    "net_password" : ""
}
configDefaults = configData

def clamp(value, minValue, maxVale):
    return min(maxValue, max(value, minValue))

def saveConfig():
    import ujson
    global configData
    with open("configData.json", "w") as f:
        ujson.dump(configData, f)
    print("Config Data Saved.")

def loadConfig():
    import ujson
    global configData
    try:
        with open("configData.json", "r") as f:
            fileData = ujson.load(f)

        for key, value in fileData.items():
            configData[key] = value
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
    "default",
    "rainbow",
    "random_strips",
    "black_and_white",
    "green_strips",
    "green_pong"
]
fixedColourDict = {
    "off" : (0, 0, 0),
    "red" : (255, 0, 0),
    "green" : (0, 255, 0),
    "blue" : (0, 0, 255),
    "white" : (255, 255, 255),
    "dark_green" : (0, 100, 0),
    "purple" : (255, 0, 255),
    "violet" : (148,0,211),
    "yellow" : (255, 226, 0),
    "orange" : (255, 145, 0),
    "cyan" : (0, 255, 255)
}
patternList.append(fixedColourDict.keys())

def ledWorker():
    global shuttingDown, LEDCOUNT, ledPin, currentPattern, neoPix, fixedColourDict
    
    pongPos = 0
    pongWidth = 15
    pongDirection = True

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
        direction = choice([True, False])
        fromPix = randint(0, int(LEDCOUNT / 2))
        for i in range(fromPix, randint(fromPix, LEDCOUNT)):
            pix[i] = cColour
            if counter == 0:
                if blank:
                    cColour = blankColour
                    blank = False
                else:
                    cColour = (randint(0, 255), randint(0, 255), randint(0, 255)) if (random) else colour
                    blank = True
                
                if direction:
                    counter = randint(5, 30)
                else:
                    counter = -randint(5, 30)
                
            if direction:
                counter -= 1
            else:
                counter += 1
            pix.write()

    def pong(pix, random=False, colour = (0, 255, 0), blankColour = (0,0,0)):
        global pongDirection, pongPos, pongWidth
        cColour = (randint(0, 255), randint(0, 255), randint(0, 255)) if (random) else colour
        
        for i in range(0, LEDCOUNT - 1):
            if i in range(pongPos, clamp(pongPos + pongWidth, 0, LEDCOUNT)):            
                pix[i] = cColour
            else:
                pix[i] = blankColour
        
        if pongDirection:
            pongPos += 1
            if pongPos >= LEDCOUNT:
                pongDirection = True
        else:
            pongPos -= 1
            if pongPos <= 0:
                pongDirection = False

        pix.write()
        
    
    neoPix = neopixel.NeoPixel(ledPin, LEDCOUNT)
    applyColour(neoPix, False)

    sleep(0.5)
    applyColour(neoPix, False, (255, 255, 255))
    sleep(0.5)
    applyColour(neoPix, False, (0, 0, 0))
    sleep(0.5)
    
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
            randomStrips(neoPix, False, blankColour = (0, 0, 0))
        elif currentPattern == "black_and_white":
            randomStrips(neoPix, False, (255, 255, 255))
        elif currentPattern == "green_pong":
            pong(neoPix, False)
        sleep(0.1)

loadConfig()
updateState()
saveConfig()

print(f"ESP32 LED Controller : Version: {VERSION} Credits: {CREDITS}")
#Networking Section
netSSID = configData["net_ssid"]
netPassword = configData["net_password"]

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
def replyJson(client, data, statusCode = 200):
    import ujson
    body = ujson.dumps(data).encode()
    client.sendall(f'HTTP/1.1 {statusCode} OK\r\n'.encode())
    client.sendall(b'Content-Type: application/json\r\n')
    client.sendall(b'Connection: close\r\n')
    client.sendall(f'Content-Length: {len(body)}\r\n\r\n'.encode())
    client.sendall(body)
    client.close()
    
def sCleanup(stringContent):
    import re
    return re.sub(r'[^A-Za-z0-9_]', '', stringContent)

def distributeModeUpdate(slaveList):
    import urequests
    errorList = []
                                
    for node in slaveList:
        url = f"http://{node}:5000/mode?pattern={currentPattern}"
                                    
        try:
            response = urequests.get(url)
            if response.status_code == 500:
                errorList.append(f"{node} ran into error {response.text}")
                continue
            
            elif response.status_code == 200:
                print("Node Updated Success.")
                
            response.close()
        except Exception as e:
            print(f"Request failed: {e}")
            
    return errorList

if configData["auto_update_check"]:
    checkForUpdates()

webAddr = (deviceIP, 5000)
webSocket = socket.socket()
webSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
webSocket.bind(webAddr)
webSocket.listen(1)

print(f"Socket Started on: {webAddr}")
print("Now Starting LED thread...")
_thread.start_new_thread(ledWorker, ())

if configData["mode"] == 1 and configData["on_boot_distribute"]:
    slaveList = configData["slave_nodes"]
    if not len(slaveList) <= 0:
        errorList = distributeModeUpdate(slaveList)
    if len(errorList) != 0:
        print(f"On boot distribute : {errorList}")

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
      
        print(f"URL: {requestURL} Params: {paramsList} IP: {clientAddr[0]}")
        
        if requestURL.count("updatesoftware") != 0:
            if paramLength == 0:
                replyJson(client, {"Message" : "Checking for updates now."})
                checkForUpdates(True)
            else:
                replyJson(client, {"Error" : "Parameter provided for a command that doesn't take any?"})

        elif requestURL.count("listpatterns") != 0:
            replyJson(client, {"Message" : "Here are all the available patterns.", "Patterns" : patternList})
        
        elif requestURL.count("ledon") != 0:
            if configData["mode"] == 2 and not clientAddr[0] in configData["slave_nodes"]:
                replyJson(client, {"Message" : "Error", "Error" : "This node is setup as a Slave node you can't change controllers state directly." }, 500)
            else:
                currentPattern = "default"
                updateState()
                if configData["mode"] == 1:
                    slaveList = configData["slave_nodes"]
                    if len(slaveList) <= 0:
                        replyJson(client, {"Warning" : "Controller setup as a master with no nodes configured?"})
                    else:
                        errorList = distributeModeUpdate(slaveList)             
                        replyJson(client, {"Message" : "Updates Distrubuted...", "Errors:" : errorList})
                else:
                    replyJson(client, {"Message" : "Started...", "CurrentPattern" : currentPattern })
            
        elif requestURL.count("ledoff") != 0:
            if configData["mode"] == 2 and not clientAddr[0] in configData["slave_nodes"]:
                replyJson(client, {"Message" : "Error", "Error" : "This node is setup as a Slave node you can't change controllers state directly." }, 500)
            else:
                currentPattern = "off"
                updateState()
                if configData["mode"] == 1:
                    slaveList = configData["slave_nodes"]
                    if len(slaveList) <= 0:
                        replyJson(client, {"Warning" : "Controller setup as a master with no nodes configured?"})
                    else:
                        errorList = distributeModeUpdate(slaveList)             
                        replyJson(client, {"Message" : "Updates Distrubuted...", "Errors:" : errorList})
                else:
                    replyJson(client, {"Message" : "Started...", "CurrentPattern" : currentPattern })
            
        elif requestURL.count("configstatus") != 0:
            data = {"Message" : "Config Data"}
            tempData = configData.copy()
            tempData.pop("net_password")
            data.update(tempData)
            replyJson(client, data)
            
        elif requestURL.count("status") != 0:
            replyJson(client,
                      {
                          "Message" : "My Status",
                          "CurrentPattern" : currentPattern,
                          "IP": webAddr,
                          "WifiName" : netSSID,
                          "LEDCount" : LEDCOUNT,
                          "Version" : VERSION
                          })
            
        elif requestURL.count("configset") != 0:
            if paramLength <= 0 or paramLength >= 2:
                replyJson(client, {"Message" : "Error", "Error" : "Too many parameters or no parameters given." }, 500)
            else:
                param = paramsList[0]
                if param[0] in configData.keys():
                    valueType = type(configData[param[0]])
                    configData[param[0]] = valueType(param[1])
                    replyJson(client, {"Message" : "Updated Value", f"{param[0]}" : f"{param[1]}" })
                    saveConfig()
                else:
                    replyJson(client, {"Message" : "Error", "Error" : "The given name doesn't exist?" }, 500)
                    
        elif requestURL.count("slavelist") != 0:
            if paramLength <= 0 or paramLength >= 2:
                replyJson(client,  {"Message" : "Error", "Error" : "Too many parameters or no parameters given." }, 500)
            else:
                param = paramsList[0]
                if param[0] == "add":
                    filterIP = param[1].replace("_", ".")
                    slaveList = configData["slave_nodes"]
                    if filterIP in slaveList:
                        replyJson(client, {"Message" : "Error", "Error" : "Can't add an already exist node / IP to the list." }, 500)
                    else:
                        slaveList.append(filterIP)
                        configData["slave_nodes"] = slaveList
                        saveConfig()
                        replyJson(client, {"Message" : "Added new Node", "Node IP" : f"{filterIP}" })
                    
                elif param[0] == "remove":
                    filterIP = param[1].replace("_", ".")
                    slaveList = configData["slave_nodes"]
                    if filterIP in slaveList:
                        slaveList.remove(filterIP)
                        configData["slave_nodes"] = slaveList
                        saveConfig()
                        replyJson(client, {"Message" : "Removed the requested Node", "Node IP" : f"{filterIP}" })
                    else:
                        replyJson(client, {"Message" : "Error", "Error" : "Can't remove a node / IP thats no in the list." }, 500)
                else:
                    replyJson(client, {"Message" : "Error", "Error" : "Provided command is invalid? Use add to add new nodes or remove to remove a node from the list." }, 500)
        
        elif requestURL.count("setmaster") != 0:
            if paramLength <= 0 or paramLength >= 2:
                replyJson(client, {"Message" : "Error", "Error" : "Too many parameters or no parameters given." }, 500)
            else:
                param = paramsList[0]
                if param[0] == "hostname":
                    filterIP = param[1].replace("_", ".")
                    configData["master_to"] = filterIP
                    saveConfig()
                    replyJson(client, {"Message" : "Node master has been updated...", "IP" : f"{filterIP}", "Note" : "For this to truly work you must update the mode aswell." })
        
        elif requestURL.count("resetconfig") != 0:
            #TODO Add a password here
            configData = configDefaults
            saveConfig()
            replyJson(client, {"Message" : "Config completely reset."}) 
                    
        elif requestURL.count("mode") != 0:
            masterNodeIP = configData["master_to"]
            if configData["mode"] == 2 and not clientAddr[0] == masterNodeIP:
                replyJson(client, {"Message" : "Error", "Error" : "Node is set in slave mode send commands to the master node.", "MasterNodeIP" : masterNodeIP }, 500)
                continue
            
            if paramLength <= 0 or paramLength >= 2:
                replyJson(client, {"Message" : "Error", "Error" : "Too many parameters or no parameters given." }, 500)
            else:
                param = paramsList[0]
                if param[0] == "pattern":
                    if param[1] in patternList:
                        currentPattern = param[1]
                        updateState()
                        
                        if configData["mode"] == 1:
                            slaveList = configData["slave_nodes"]
                            if len(slaveList) <= 0:
                                replyJson(client, {"Warning" : "Controller setup as a master with no nodes configured?"})
                            else:
                                errorList = distributeModeUpdate(slaveList)
                                        
                                replyJson(client, {"Message" : "Updates Distrubuted...", "Errors:" : errorList})
                        else:
                            replyJson(client, {"Message" : "Updated Mode", "CurrentPattern" : currentPattern })
                    else:
                        replyJson(client, {"Message" : "Error", "Error" : "Provided pattern isn't within the list?" }, 500)
                else:
                    replyJson(client, {"Message" : "Failed", "Error" : "Provided data name abnormally or incorrectly provided Ensure naming is correct." }, 500)
                    
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


