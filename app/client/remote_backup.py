import os
import threading
import baksys.config  as config
from   baksys.net     import *
import app.com.packet as packet

class BaksysRemoteBackup:
    def __init__(this):
        this.socket         = BaksysClientSocket()
        this.responseLock   = threading.Event()
        this.remoteResponse = None
        
    def isConnecting(this):
        return this.socket.isConnecting()
        
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
        
    def disconnect(this):
        this.socket.disconnect()
        
    def login(this, username, password):
        this.socket.send(packet.loginRequest(username, password))
        return this._waitForResponse()
        
    def getUpdateList(this, localList):
        this.socket.send(packet.updateListRequest(localList))
        return this._waitForResponse()
        
    def getList(this):
        this.socket.send(packet.backupListRequest())
        return this._waitForResponse()
        
    def uploadBackup(this, backup, path):
        # TODO
        pass
        
    def deleteBackup(this, name):
        this.socket.send(packet.backupDeleteRequest(name))
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
        result =  this.remoteResponse['result']
        this.remoteResponse = None
        return result
    
    def _onConnectReset(this, socket):
        this._setResponseError('disconnect from server')
            
    def _setResponseError(this, message):
        if this.remoteResponse:
            this.remoteResponse['error'] = message
            this.responseLock.set()
            
    def _setResponse(this, result):
        if this.remoteResponse:
            this.remoteResponse['result'] = result
            this.responseLock.set()
        
    def _onPacket(this, socket, message):
        header = message.readByte()
        
        if   header == packet.BAKSYS_LOGIN_RESPONSE:
            this._setResponse(message.readByte() == 1)
            
        elif header == packet.BAKSYS_LIST_RESPONSE:
            count = message.readEncodingInt()
            backupList = []
            for i in range(count):
                path    = message.readString()
                orgpath = message.readString()
                size    = message.readLong()
                crc     = message.readUInt()
                backupList.append({                         \
                    'name'        : os.path.basename(path), \
                    'path'        : path,                   \
                    'origin_path' : orgpath,                \
                    'size'        : size,                   \
                    'crc'         : crc,                    \
                })
            this._setResponse(backupList)
            
        elif header == packet.BAKSYS_UPDATE_LIST_RESPONSE:
            count = message.readEncodingInt()
            updateList = []
            for i in range(count):
                updateList.append(message.readString())
            this._setResponse(updateList)
            
        elif header == packet.BAKSYS_DELETE_RESPONSE:
            success = (message.readByte() == 1)
            if success:
                this._setResponse(success)
            else:
                this._setResponseError(message.readString())
            
        elif header == packet.BAKSYS_LOGIN_RESPONSE:
            this._setResponse(message.readByte() == 1)
        else:
            # TODO: process invalid packet
            pass