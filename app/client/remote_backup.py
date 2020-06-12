import os
import shutil
import threading
from   random              import random
from   baksys.net          import *
from   baksys.event        import *
from   app.client.setting  import *
import app.com.packet        as packet
import app.com.packet.login  as loginPacket
import app.com.packet.backup as backupPacket

class BaksysRemoteBackup:
    def __init__(this):
        this.socket             = BaksysClientSocket()
        this.responseLock       = threading.Event()
        this.remoteResponse     = { }
        this.fileOperation      = { }
        this.lastOperationError = ''
        this.onDownloadProcess  = BaksysEvent()
        
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
        this.socket.send(loginPacket.loginRequest(username, password))
        return this._waitForResponse()
        
    def getUpdateList(this, localList):
        this.socket.send(backupPacket.updateListRequest(localList))
        return this._waitForResponse()
        
    def getList(this):
        this.socket.send(backupPacket.listRequest())
        return this._waitForResponse()
        
    def downloadInterrupt(this):
        this.socket.send(backupPacket.downloadBreakRequest())
        
    def handleDownload(this, message):
        subtype = message.readByte()
        if   subtype == backupPacket.UPLOAD_DOWNLOAD_CONTINUE:
            try:
                if not this.fileOperation:
                    this.downloadInterrupt()
                    return
                offset = message.readLong()
                size   = message.readLong()
                data   = message.readBuffer(size)
                this.fileOperation['offset'] = offset
                this.fileOperation['size']  += size
                this.fileOperation['file'].seek(offset, 0)
                this.fileOperation['file'].write(data)
                
                # event invoke
                args = BaksysEventArgs()
                args.progress = this.fileOperation['size'] / this.fileOperation['total_size']
                this.onDownloadProcess.invoke(args)
            except Exception as e:
                this.downloadInterrupt()
                this.lastOperationError = str(e)
                this._setResponse(False)
                
        elif subtype == backupPacket.UPLOAD_DOWNLOAD_FINISH:
            if not this.fileOperation:
                this.downloadInterrupt()
                return
            this.fileOperation['file'].close()
            shutil.move(this.fileOperation['temp'], this.fileOperation['path'])
            this.fileOperation = {}
            this._setResponse(True)
            
        elif subtype == backupPacket.UPLOAD_DOWNLOAD_BREAK:
            this.lastOperationError = 'operation has been interrupted by remote server'
            this._setResponse(False)
            
        elif subtype == backupPacket.UPLOAD_DOWNLOAD_START:
            this.fileOperation['total_size'] = message.readLong()
            this._setResponse(True)
            
    def downloadRequest(this, path):
        temppath = ''
        while temppath == '' or os.path.exists(temppath):
            temppath = os.path.join(BAKSYS_TEMPDIR, 'download_%08X'%int(random()*0x100000000))
        this.fileOperation = {                                        \
            'path'       : os.path.join(config['backup_path'], path), \
            'temp'       : temppath,                                  \
            'file'       : None,                                      \
            'offset'     : 0,                                         \
            'size'       : 0,                                         \
            'total-size' : 0                                          \
        }
        if not os.path.exists(BAKSYS_TEMPDIR):
            os.makedirs(BAKSYS_TEMPDIR)
        this.fileOperation['file'] = open(this.fileOperation['temp'], 'wb')
        this.socket.send(backupPacket.downloadRequest(path))
        return this._waitForResponse()
            
    def downloadBackup(this):
        if not this.fileOperation:
            this.lastOperationError = 'not any download request.'
            return False
        return this._waitForResponse()
        
    def uploadBackup(this, backup, path):
        # TODO
        pass
        
    def deleteBackup(this, name):
        this.socket.send(backupPacket.deleteRequest(name))
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
        this.remoteResponse = { }
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
        
        if   header == packet.RESPONSE_OPERATION:
            success = (message.readByte() == 1)
            if not success:
                this.lastOperationError = message.readString()
            this._setResponse(success)
            
        elif header == packet.RESPONSE_BACKUP:
            subtype = message.readByte()
            if subtype == backupPacket.REQUEST_TYPE_LIST:
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
            elif subtype == backupPacket.REQUEST_TYPE_UPDATE_LIST:
                count = message.readEncodingInt()
                updateList = []
                for i in range(count):
                    updateList.append(message.readString())
                this._setResponse(updateList)
            
        elif header == packet.RESPONSE_DOWNLOAD:
            this.handleDownload(message)
            
        else:
            # TODO: process invalid packet
            pass