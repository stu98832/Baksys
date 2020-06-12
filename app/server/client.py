import os
import app.server.handler    as handler
import app.com.packet        as packet

class BaksysUser:
    def __init__(this, socket):
        this.login               = False
        this.username            = ''
        this.socket              = socket
        this.socket.onReceive    = this._handleMessage
        this.socket.onDisconnect = this._onDisconnect
        this.onDisconnect        = lambda s: None
        this.socket.startReceive()
        
    def __del__(this):
        this.socket.close()
        
    def _onDisconnect(this, socket):
        this.socket.close()
        this.onDisconnect(this)
        
    def _checkLogin(this):
        if not this.login:
            this.socket.disconnect()
        return this.login
        
    def _handleMessage(this, socket, message):
        header = message.readByte()
        if   header == packet.REQUEST_LOGIN:
            username = message.readString()
            password = message.readString()
            handler.handleLogin(this, username, password)
            
        elif header == packet.REQUEST_BACKUP:
            if this._checkLogin():
                handler.handleBackupRequest(this, message)
                
        elif header == packet.REQUEST_DOWNLOAD:
            if this._checkLogin():
                handler.handleDownloadRequest(this, message)
            
        else:
            pass
        