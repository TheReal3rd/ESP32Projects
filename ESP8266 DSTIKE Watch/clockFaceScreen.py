from screens.templateScreen import *
import gc
import os
        
class clockFaceScreen(templateScreen):
    def __init__(self, i2c):
        import ds3231
        rtc = ds3231.DS3231(i2c, addr=104)
        self._rtc = rtc
        super().__init__(False)
        
    def flashMemStats(self):
        fs = os.statvfs('/')
        block = fs[0]
        return ( (block * fs[2]) // 1024, (block * fs[3]) // 1024 )
    
    def format12Hour(self, hour, minute, second):
        amPM = "AM"
        if hour == 0:
            hour_12 = 12
        elif hour > 12:
            hour_12 = hour - 12
            amPM = "PM"
        elif hour == 12:
            hour_12 = 12
            amPM = "PM"
        else:
            hour_12 = hour
        return f"{hour_12:02d}:{minute:02d}:{second:02d} {amPM}"

    def show(self, oled):
        if not self._rtc:
            oled.text("RTC Error", 0, 0)
            return
            
        date = self._rtc.datetime()
        oled.text(self.format12Hour(date[3], date[4], date[5]), 0, 0)
        oled.text(f"{date[2]:02d}-{date[1]:02d}-{date[0]:04d}", 0, 10)
        
        total, used = self.flashMemStats()
        oled.text(f"F: {total}/{used}", 0, 35)
        
        oled.text(f"H-A:{gc.mem_alloc() // (1024)}kb", 0, 45)
        oled.text(f"H-F:{gc.mem_free() // (1024)}kb", 0, 55)
        
    def selectButton(self):
        if self._ready:
            import utils
            utils.showSelectScreen()

