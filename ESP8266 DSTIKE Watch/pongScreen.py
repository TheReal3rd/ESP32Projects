from screens.templateScreen import *
from vector2F import *


class pongScreen(templateScreen):
    leftScore = 0
    rightScore = 0
    leftPadalVec = Vector2F(5, 32)
    rightPadalVec = Vector2F(123, 32)
    ballVec = Vector2F(64, 32)
    ballSize = 5
    ballHalfSize = int(ballSize / 2) 
    
    ballVelVec = Vector2F(0, 1)
    
    dirList = [-1.0, -0.7, -0.5, 0.0, 0.5, 0.7, 1.0]
    
    def __init__(self):
        super().__init__(buttonLoop = True)
        
    def drawBall(self, oled, posVec):
        for xOffset in range(int(posVec.x - self.ballHalfSize), int(posVec.x + self.ballHalfSize) + 1):
            oled.vline(xOffset, int(posVec.y - self.ballHalfSize), self.ballSize, 1)
            
    def drawPadal(self, oled, posVec, height):
        oled.vline(int(posVec.x), int(posVec.y - (height / 2)), height, 2)
        
    def resetBall(self):
        self.ballVec = Vector2F(64, 32)
        self.ballVelVec.x *= -1
        self.ballVelVec.y = self.dirList[randint(0, len(self.dirList) - 1)]
        
    def show(self, oled):
        from utils import randint
        self.drawBall(oled, self.ballVec)
        self.drawPadal(oled, self.leftPadalVec, 21)
        self.drawPadal(oled, self.rightPadalVec, 21)
        oled.text(str(self.leftScore), 2, 0)
        oled.text(str(self.rightScore), 120, 0)
        
        self.ballVec += self.ballVelVec
        
        if self.ballVec.y >= 62 or self.ballVec.y <= 2:
            self.ballVelVec.x = self.dirList[randint(0, len(self.dirList) - 1)]
            self.ballVelVec.y *= -1
            
        #if int(self.ballVec.y) in range(int(self.leftPadalVec.y - self.ballHalfSize), int(self.leftPadalVec.y + self.ballHalfSize)) and
        #    int(self.ballVec.x) <= :
            
        if self.ballVec.x <= 0:
            self.leftScore += 1
            self.resetBall()
        elif self.ballVec.x >= 128:
            self.rightScore += 1
            self.resetBall()
    
    def upButton(self):
        from utils import clamp
        self.rightPadalVec.y -= 2
        self.rightPadalVec.y = clamp(self.rightPadalVec.y, 10, 54)
    
    def downButton(self):
        from utils import clamp
        self.rightPadalVec.y += 2
        self.rightPadalVec.y = clamp(self.rightPadalVec.y, 10, 54)
    
    def selectButton(self):
        if self._ready:
            import utils
            utils.showSelectScreen()
           

