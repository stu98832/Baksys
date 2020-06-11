class BaksysEvent:
    def __init__(this):
        this.registers = []
        
    def add(this, func):
        this.registers.append(func)
        
    def remove(this, func):
        if func in this.registers:
            this.registers.remove(func)
            
    def invoke(this, *args):
        for func in this.registers:
            func(*args)
            
    def __iadd__(this, func):
        this.add(func)
        return this
        
    def __isub__(this, func):
        this.remove(func)
        return this
# end BaksysEvent

class BaksysEventArgs:
    def __init__(this):
        pass