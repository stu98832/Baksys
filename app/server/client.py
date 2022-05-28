import os
from   app.server     import handler
import app.com.packet as packet

class BaksysUser:
    def __init__(this, socket):
        this.login               = False
        this.username            = ''
        this.socket              = socket
        this.socket.onReceive    = this.handleMessage
        this.socket.onDisconnect = this.onDisconnect
        this.onDisconnect        = lambda s: None
        this.socket.startReceive()
        
    def __del__(this):
        this.socket.close()
        
    def onDisconnect(this, socket):
        if this.login:
            this.backup.uploadInterrupted = True
            this.backup.acceptUploadInterrutpt()
        this.socket.close()
        this.onDisconnect(this)
        
    def checkLogin(this):
        if not this.login:
            this.socket.disconnect()
        return this.login
        
    def handleMessage(this, socket, message):
        header = message.readByte()
        if   header == packet.REQUEST_LOGIN:
            username = message.readString()
            password = message.readString()
            handler.handleLogin(this, username, password)
            
        elif header == packet.REQUEST_BACKUP:
            if this.checkLogin():
                handler.handleBackupRequest(this, message)
                
        elif header == packet.REQUEST_UPLOAD:
            if this.checkLogin():
                handler.handleUploadRequest(this, message)
                
        elif header == packet.REQUEST_DOWNLOAD:
            if this.checkLogin():
                handler.handleDownloadRequest(this, message)
            
        else:
            pass
        