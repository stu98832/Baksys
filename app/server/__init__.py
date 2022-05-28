import os
import threading
from   baksys.net            import *
from   app.server.setting    import *
from   app.server.client     import *

class BaksysServerApp:
    def __init__(this):
        this.commands = { }
        this.users    = [ ]
        this._loadCommands()
        this.socket = BaksysServerSocket()
        this.socket.onAccept = this._onAccept
        
    def _loadCommands(this):
        this.commands['exit']    = { 'desc':'exit this program' }
        this.commands['help']    = { 'desc':'show help message', \
            'func':this.cmdHelp }
        
    def cmdHelp(this):
        maxlen = 0
        for cmd in this.commands:
            maxlen = max(maxlen, len(cmd))
            
        fmt = '%%-%ds : %%s' % (maxlen)
        for cmd in this.commands:
            print(fmt % (cmd, this.commands[cmd]['desc']))
        
    def _onUserDisconnect(this, client):
        this.users.remove(client)
        
    def _onAccept(this, server, socket):
        user = BaksysUser(socket)
        user.onDisconnect = this._onUserDisconnect
        this.users.append(user)
    
    def run(this):
        this.socket.start('0.0.0.0', BAKSYS_PORT)
        this.socket.startAccept()
        cmdThread = threading.Thread(target = this.commandMode, daemon = True)
        cmdThread.start()
        while this.socket.isListening():
            import time
            time.sleep(1)
        
    def commandMode(this):
        if not this.socket.isListening():
            return
        print('server has listened on port %d' % BAKSYS_PORT)
        print('\'help\' to show help message')
        while True:
            try:
                cmd = input('> ')
                
                if cmd == 'exit':
                    saveConfig()
                    this.onExit()
                    print('see you~')
                    break
                elif cmd in this.commands:
                    this.commands[cmd]['func']()
                else:
                    print('can\'t find command \'%s\'' % cmd)
            except KeyboardInterrupt:
                print('^C')
        
    def onExit(this):
        userList = this.users
        for user in userList:
            this.users.remove(user)
        this.socket.close()
# end BaksysServerApp