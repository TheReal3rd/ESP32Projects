class templateScreen():
    #Loops button input when held pressed.
    _buttonInputLoop = False
    _ready = False
    
    def __init__(self, buttonLoop = False):
        self._buttonInputLoop = buttonLoop
        self._ready = True

    def show(self, oled):
        pass
    
    def upButton(self):
        pass
    
    def downButton(self):
        pass
    
    def selectButton(self):
        pass
    
    def isButtonLoop(self):
        return self._buttonInputLoop
    
    def isReady(self):
        return self._ready

