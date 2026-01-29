from screens.templateScreen import *
from screens.selectMenuScreen import *

class dvdScreen(templateScreen):
    xPos = 64
    yPos = 32
    dirList = [-1.0, -0.5, 0.5, 1.0]
    xVel = 0.0
    yVel = 0.0
    
    def __init__(self):
        from utils import randint
        self.xVel = self.dirList[randint(0, len(self.dirList) - 1)]
        self.yVel = self.dirList[randint(0, len(self.dirList) - 1)]
        super().__init__()
    
    def show(self, oled):
        oled.text("DVD", int(self.xPos), int(self.yPos))
        oled.rect(int(self.xPos) - 1, int(self.yPos) - 2, 25, 12)
        
        self.xPos += self.xVel
        self.yPos += self.yVel
        
        intXPos = int(self.xPos)
        intYPos = int(self.yPos)
        if intXPos <= 1 or intXPos >= 103:
            self.xVel *= -1
        if intYPos <= 2 or intYPos >= 54:
            self.yVel *= -1
        
    def selectButton(self):
        if self._ready:
            import utils
            utils.showSelectScreen()

