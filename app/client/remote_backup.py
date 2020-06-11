import os
import threading
import baksys.config  as config
from   baksys.backup  import *
from   baksys.event   import *
from   baksys.net     import *
import app.com.packet as packet

class BaksysRemoteBackup:
    def __init__(this):
        this.socket       = BaksysClientSocket()
        this.responseLock = threading.Event()
        
    def connect(this, address, port):
        if this.socket.isConnecting():
            return True
            
        try:
            this.socket.connect(address, port)
            this.socket.onReceive    = this._onPacket
            this.socket.onDisconnect = this._onConnectReset
            this.socket.startReceive()
        except Exception as e:
            return False
        return True
        
    def login(this, username, password):
        this.socket.send(packet.loginRequest(username, password))
        return this._waitForResponse()
        
    def getUpdateList(this, localList):
        this.socket.send(packet.updateListRequest(localList))
        return this._waitForResponse()
            
    def _waitForResponse(this):
        this.remoteResponse = {\
            'result'   : None, \
            'error'    : None
        }
        this.responseLock.clear()
        this.responseLock.wait()
        if this.remoteResponse['error']:
            raise RuntimeError(this.remoteResponse['error'])
        return this.remoteResponse['result']
    
    def _onConnectReset(this, socket):
        this._setResponseError('disconnect from server')
            
    def _setResponseError(this, message):
        this.remoteResponse['error']    = message
        this.responseLock.set()
            
    def _setResponse(this, result):
        this.remoteResponse['result']   = result
        this.responseLock.set()
        
    def _onPacket(this, socket, message):
        header = message.readByte()
        if   header == packet.BAKSYS_UPDATE_LIST_RESPONSE:
            count = message.readEncodingInt()
            updateList = []
            for i in range(count):
                updateList.append(message.readString())
            this._setResponse(updateList)
        elif header == packet.BAKSYS_LOGIN_RESPONSE:
            this._setResponse(message.readByte() == 1)
        elif header == packet.BAKSYS_UPLOAD_RESPONSE:
            this._setResponse(message.readByte() == 1)
        else:
            # TODO: process invalid packet
            pass