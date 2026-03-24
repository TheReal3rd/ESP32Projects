from screens.templateScreen import *

class selectMenuScreen(templateScreen):
    
    def __init__(self, options, buttonLoop = False):
        self.sIndex = 0
        self.optionsDict = options
        self.keysCach = list(options.keys())
        self.keysCach.sort()
        super().__init__(buttonLoop)
        
    def show(self, oled):
        yOffset = 0
        keyList = self.keysCach
        for keyIndex in range(0, len(keyList)):
            key = keyList[keyIndex].upper()
            if keyIndex == self.sIndex:
                oled.text(f">{key}<", int(64 - (len(key) * 5)), yOffset)
            else:
                oled.text(f" {key} ", int(64 - (len(key) * 5)), yOffset)
            yOffset += 10
            
    def upButton(self):
        from utils import clamp
        self.sIndex -= 1
        self.sIndex = clamp(self.sIndex, 0, len(self.keysCach) - 1)
        
    def downButton(self):
        from utils import clamp
        self.sIndex += 1
        self.sIndex = clamp(self.sIndex, 0, len(self.keysCach) - 1)
        
    def selectButton(self):
        if self._ready:
            func = self.optionsDict[self.keysCach[self.sIndex]]
            if func:
                func()
            else:
                print("No function defined.")


