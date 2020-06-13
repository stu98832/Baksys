import os
import time
import threading
from   random              import random
from   baksys.net          import *
from   baksys.event        import *
from   app.client.setting  import *
import app.client.handler    as handler
import app.com.packet        as packet
import app.com.packet.login 
import app.com.packet.backup 

class BaksysRemoteBackup:
    def __init__(this):
        this.socket             = BaksysClientSocket()
        this.responseLock       = threading.Event()
        this.remoteResponse     = { }
        this.downloadFile       = { }
        this.lastOperationError = ''
        this.onDownloadProcess  = BaksysEvent()
        
    def isConnecting(this):
        return this.socket.isConnecting()
        
    def connect(this, address, port):
        if this.socket.isConnecting():
            return True
            
        try:
            this.socket.connect(address, port)
            this.socket.onReceive    = this.onPacket
            this.socket.onDisconnect = this.onConnectReset
            this.socket.startReceive()
        except Exception as e:
            return False
        return True
        
    def disconnect(this):
        this.socket.disconnect()
        
    def login(this, username, password):
        this.socket.send(packet.login.loginRequest(username, password))
        return this.waitForResponse()
        
    def getUpdateList(this, localList):
        this.socket.send(packet.backup.updateListRequest(localList))
        return this.waitForResponse()
        
    def getList(this):
        this.socket.send(packet.backup.listRequest())
        return this.waitForResponse()
        
    def downloadInterrupt(this):
        this.socket.send(packet.backup.downloadBreakRequest())
        if this.downloadFile['file']:
            this.downloadFile['file'].close()
            os.remove(this.downloadFile['temp'])
        this.downloadFile = { }
            
    def downloadRequest(this, path):
        temppath = ''
        while temppath == '' or os.path.exists(temppath):
            temppath = os.path.join(BAKSYS_TEMPDIR, 'download_%08X'%int(random()*0x100000000))
        this.downloadFile = {                                         \
            'path'       : os.path.join(config['backup_path'], path), \
            'temp'       : temppath,                                  \
            'file'       : None,                                      \
            'offset'     : 0,                                         \
            'size'       : 0,                                         \
            'total-size' : 0                                          \
        }
        if not os.path.exists(BAKSYS_TEMPDIR):
            os.makedirs(BAKSYS_TEMPDIR)
        this.downloadFile['file'] = open(this.downloadFile['temp'], 'wb')
        this.socket.send(packet.backup.downloadRequest(path))
        return this.waitForResponse()
    # end downloadRequest
            
    def downloadBackup(this):
        if not this.downloadFile:
            this.lastOperationError = 'no avaiable download request.'
            return False
        return this.waitForResponse()
        
    def uploadBackup(this, backup, path):
        # TODO
        pass
        
    def deleteBackup(this, name):
        this.socket.send(packet.backup.deleteRequest(name))
        return this.waitForResponse()
            
    def waitForResponse(this):
        this.remoteResponse = {\
            'result'   : None, \
            'error'    : None
        }
        this.responseLock.clear()
        while not this.responseLock.is_set():
            time.sleep(0.1)
        if this.remoteResponse['error']:
            raise RuntimeError(this.remoteResponse['error'])
        result =  this.remoteResponse['result']
        this.remoteResponse = { }
        return result
    # end waitForResponse
    
    def onConnectReset(this, socket):
        this.setResponseError('disconnect from server')
            
    def setResponseError(this, message):
        if this.remoteResponse:
            this.remoteResponse['error'] = message
            this.responseLock.set()
            
    def setResponse(this, result):
        if this.remoteResponse:
            this.remoteResponse['result'] = result
            this.responseLock.set()
        
    def onPacket(this, socket, message):
        header = message.readByte()
        
        if   header == packet.RESPONSE_OPERATION:
            success = (message.readByte() == 1)
            if not success:
                this.lastOperationError = message.readString()
            this.setResponse(success)
            
        elif header == packet.RESPONSE_BACKUP:
            handler.handleBackup(this, message)
            
        elif header == packet.RESPONSE_DOWNLOAD:
            handler.handleDownload(this, message)
            
        else:
            # TODO: process invalid packet
            pass
    # end onPacket