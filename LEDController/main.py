import sys

def executeScript(scriptPath):
    try:
        with open(scriptPath) as f:
            code = f.read()
        exec(code, {})
        return True
    except Exception as e:
        print(f"Failed to execute controller script. {e}")
        return False
    except KeyboardInterrupt as ki:
        print("Keyboard interrupt detected.")
        return True
    
if not executeScript("controller.py"):
    print("Falling back on backup controller.")
    executeScript("controller.py.bak")
