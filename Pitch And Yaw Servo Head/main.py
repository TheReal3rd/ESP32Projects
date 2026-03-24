from servo import Servo
import time
import random
import _thread
import network
import socket

global yawMotor, pitchMotor, lastPos, currentPos, shuttingDown, targetPos

#utilities
def clamp(value, minValue, maxValue):
    return min(maxValue, max(value, minValue))

#Motor Controls.
yawMotor=Servo(pin=0, maxAngle = 270)
pitchMotor=Servo(pin=10)

yawMotor.move(0)
pitchMotor.move(0)
lastPos = [0,0]
currentPos = lastPos
targetPos = [0,0]

shuttingDown = False

def motorHandlerThread():
    global yawMotor, pitchMotor, lastPos, currentPos, shuttingDown, targetPos
    
    targetPitch = 0
    targetYaw = 0
    
    
    while not shuttingDown:
        if currentPos[0] != targetPos[0]:
            targetPitch = targetPos[0]
            currentPos[0] = targetPitch
            
        if currentPos[1] != targetPos[1]:
            targetYaw = targetPos[1]
            yawMotor.move(targetYaw)
            currentPos[1] = targetYaw
            
        pitchMotor.move(clamp(targetPitch, 0, 180))
        yawMotor.move(clamp(targetYaw, 0, 270))
            
        time.sleep(0.1)


_thread.start_new_thread(motorHandlerThread,())

targetPos = [180, 270]
time.sleep(1)
targetPos = [0, 0]

#Networking
SSID = ""
PASSWORD = ""

wifi = network.WLAN(network.STA_IF)
wifi.active(True)

print(f"Connecting to {SSID}...")
wifi.connect(SSID, PASSWORD)

connectAttempts = 0
while not wifi.isconnected(): 
    print(".", end="")
    time.sleep(0.5)
    connectAttempts += 1
    if connectAttempts >= 10:
        exit()
        break

wifiInfo = wifi.ifconfig()
print("\nConnected!\nIP config:", wifiInfo)

deviceIP = wifiInfo[0]

def sCleanup(stringContent):
    import re
    return re.sub(r'[^A-Za-z0-9_]', '', stringContent)

def replyJson(client, data, statusCode = 200):
    import ujson
    body = ujson.dumps(data).encode()
    client.sendall(f'HTTP/1.1 {statusCode} OK\r\n'.encode())
    client.sendall(b'Content-Type: application/json\r\n')
    client.sendall(b'Connection: close\r\n')
    client.sendall(f'Content-Length: {len(body)}\r\n\r\n'.encode())
    client.sendall(body)
    client.close()

webAddr = (deviceIP, 5000)
webSocket = socket.socket()
webSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
webSocket.bind(webAddr)
webSocket.listen(1)

try:
    while not shuttingDown:
        client, clientAddr = webSocket.accept()
        rawRequest = client.recv(1024)
        requestParts = rawRequest.split()
        httpMethods = str(requestParts[0]).lower()
        requestURL = str(requestParts[1]).replace("/", "").lower()
        paramsList = {}
        paramLength = 0
        
        if httpMethods.count("post") != 0:
            print("Post Request")
            
        else:
            if requestURL.count("?") != 0:
                paramSplit = requestURL.split("?")
                requestURL = paramSplit[0]
                for param in paramSplit[1].split("&"):
                    valueSplit = param.split("=")
                    paramsList.update( { sCleanup(str(valueSplit[0].lower())) : sCleanup(str(valueSplit[1].lower()))} )
                paramLength = len(paramsList)
          
            print(f"URL: {requestURL} Params: {paramsList} IP: {clientAddr[0]}")
        
            if requestURL.count("zero") != 0:
                if paramLength == 0:
                    replyJson(client, {"Message" : "Moving to zero position."})
                    targetPos = [0, 0]
                else:
                    replyJson(client, {"Error" : "no params needed."})
            
            elif requestURL.count("to") != 0:
                if paramLength == 2:
                    if "pitch" in paramsList and "yaw" in paramsList:
                        pitch = int(paramsList["pitch"])
                        yaw = int(paramsList["yaw"])
                        targetPos = [pitch, yaw]
                        replyJson(client, { "Message" : "Moving to provided position.", "Pitch": pitch, "Yaw" : yaw  })
                    else:
                        replyJson(client, { "Error" : "Provided params are not value of pitch or yaw."})
                        
                elif paramLength == 1:
                    
                    if "pitch" in paramsList:
                        pitch = int(paramsList["pitch"])
                        targetPos[0] = pitch
                        replyJson(client, { "Message" : "Moving to provided position.", "Pitch": pitch })
                    
                    elif "yaw" in paramsList:
                        yaw = int(paramsList["yaw"])
                        targetPos[1] = yaw
                        replyJson(client, { "Message" : "Moving to provided position.", "Yaw" : yaw })
                    else:
                        replyJson(client, {"Error" : "Incorrect number of params provided."})
                else:
                    replyJson(client, {"Error" : "Incorrect number of params provided."})
            elif requestURL.count("position") != 0:
                if paramLength == 0:
                    replyJson(client, {"Message" : "Current position information", "TargetPosition" : targetPos, "CurrentPosition" : currentPos, "LastPosition" : lastPos})
                else:
                    replyJson(client, {"Error" : "no params needed."})
                    
except KeyboardInterrupt:
    shuttingDown = True
    print("Keyboard press detected.")
except Exception as er:
    print("Thrown an error: ", er)

print("Bye")




