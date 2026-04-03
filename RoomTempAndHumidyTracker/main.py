from machine import Pin, RTC, deepsleep
import time
import dht
import network
import socket
import ntptime
import urequests

#Data entry
ROOM_NAME = "BedRoom"
EXTRA_INFO = "No Extra Information"

SLEEP_DURATION = 3600000

ACTIVE_LED = Pin(21, Pin.OUT)

#Sensors
sensor = dht.DHT11(Pin(22))

#Networking
SSID = "aaa"
PASSWORD = "aaaa"
HEADERS = {"Content-Type": "application/json"}
TARGET_ADDRESS = "http://192.168.0.14:3000"

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

rtc = RTC()
if wifi.isconnected():
    try:
        ntptime.settime()
        print("RTC Sync Done.")
    except Exception as es:
        print(f"Failed RTC sync. Error: {es}")

try:
    time.sleep(2)
    sensor.measure()
    time.sleep(0.5)
    temperature = sensor.temperature()
    humidity = sensor.humidity()
    currentTime = rtc.datetime()
    print(f"Detected measurements Temperature: {temperature} Humidity: {humidity} Time: {currentTime}")
    data = {
        "name"     : ROOM_NAME,
        "extra"    : EXTRA_INFO,
        "temp"     : temperature,
        "humidity" : humidity,
        "timeDate" : currentTime
    }
    ACTIVE_LED.on()
    
    try:
        response = urequests.post(TARGET_ADDRESS, json=data, headers=HEADERS)
        if response.status_code == 200:
            print("Success:", response.json())
        else:
            print("Error:", response.status_code)
        response.close()
    except Exception:
        print("Error fix later")
    
    print("\n\nNow waiting 10 seconds Before deepsleep...")
    time.sleep(10)
    ACTIVE_LED.off()
    print("Nap time...")
    deepsleep(SLEEP_DURATION)
except KeyboardInterrupt:
    print("Shutting down")
    
