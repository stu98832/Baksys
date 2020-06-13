import os
import shutil
import threading
import time
from   random                import random
from   baksys.backup         import *
from   baksys.event          import *
from   app.server.setting    import *
import app.com.packet        as packet
import app.com.packet.backup

class BaksysUserBackup:
    UPLOAD_CHUNK_SIZE = 65535

    def __init__(this, username):
        this.backupPath   = os.path.join(config['backup_path'], username)
        this.acceptUploadFile = { }
        this.uploadThread = None
        if not os.path.exists(this.backupPath):
            os.makedirs(this.backupPath)
        
    def _checkPathValid(this, path):
        if '..' in path:
            raise RuntimeError('unsafe path \'%s\' denied!' % path)
            
    def acceptUploadInterrutpt(this):
        if this.acceptUploadFile and this.acceptUploadFile['file']:
            this.acceptUploadFile['file'].close()
            os.remove(this.acceptUploadFile['temp'])
        this.acceptUploadFile = { }
            
    def acceptUploadData(this, offset, data):
        if this.acceptUploadFile and this.acceptUploadFile['file']:
            this.acceptUploadFile['file'].seek(offset, 0)
            this.acceptUploadFile['file'].write(data)
            
    def acceptUploadFinish(this):
        if this.acceptUploadFile and this.acceptUploadFile['file']:
            this.acceptUploadFile['file'].close()
            shutil.move(this.acceptUploadFile['temp'], this.acceptUploadFile['path'])
        this.acceptUploadFile = { }
            
    def acceptUpload(this, path):
        this._checkPathValid(path)
        temppath = ''
        while temppath == '' or os.path.exists(temppath):
            temppath = os.path.join(BAKSYS_TEMPDIR, 'upload_%08X'%int(random()*0x100000000))
        this.acceptUploadFile = {                               \
            'path'       : os.path.join(this.backupPath, path), \
            'temp'       : temppath,                            \
            'file'       : None,                                \
            'offset'     : 0,                                   \
            'size'       : 0,                                   \
            'total-size' : 0,                                   \
        }
        this.acceptUploadFile['file'] = open(this.acceptUploadFile['temp'], 'wb')
            
    def startUpload(this, client, path):
        this._checkPathValid(path)
        fullpath  = os.path.join(this.backupPath, path)
        if not os.path.exists(fullpath):
            raise RuntimeError('can\'t find backup file \'%s\'' % path)
        
        def upload():
            try:
                with open(fullpath, 'rb') as file:
                    begin  = file.tell()
                    file.seek(0, 2)
                    size   = file.tell() - begin
                    offset = 0
                    file.seek(0, 0)
                    client.socket.send(packet.backup.downloadStartResponse(size))
                    while size > 0 and client.socket.isConnecting():
                        if this.uploadInterrupted:
                            client.socket.send(packet.backup.downloadBreakResponse())
                            return
                        sizeToWrite = min(this.UPLOAD_CHUNK_SIZE, size)
                        data        = file.read(sizeToWrite)
                        client.socket.send(packet.backup.downloadDataResponse(offset, data))
                        offset += sizeToWrite
                        size   -= sizeToWrite
                client.socket.send(packet.backup.downloadFinishResponse())
            except Exception as e:
                logger.error('error during upload file', e)
                client.socket.send(packet.backup.downloadBreakResponse())
        
        this.uploadInterrupted = False
        this.uploadThread = threading.Thread(target=upload)
        this.uploadThread.start()
        
    def getBackup(this, path):
        this._checkPathValid(path)
        backupFile = os.path.join(this.backupPath, path)
        
        if not os.path.exists(backupFile):
            return None
        
        backup = BaksysBackup()
        backup.load(backupFile)
        return backup
        
    def deleteBackup(this, path):
        this._checkPathValid(path)
        fullpath  = os.path.join(this.backupPath, path)
        
        if not os.path.exists(fullpath):
            raise RuntimeError('can\'t find backup file \'%s\'' % path)
            
        os.remove(fullpath)
        
    def getList(this):
        result = []
        queue  = []
        
        if os.path.exists(this.backupPath):
            queue.insert(0, '')
        
        while len(queue) > 0:
            dirpath  = queue.pop()
            dirname = os.path.join(this.backupPath, dirpath)
            for name in os.listdir(dirname):
                itempath = os.path.join(dirpath, name)
                itemname = os.path.join(dirname, name)
                if os.path.isdir(itemname):
                    queue.insert(0, itempath)
                else:
                    backup = BaksysBackup()
                    backup.load(itemname)
                    result.append({\
                        'name'        : backup.sName, \
                        'path'        : itempath,     \
                        'origin_path' : backup.sPath, \
                        'size'        : backup.nSize, \
                        'crc'         : backup.nCRC   \
                    })
                    backup.close()
                    
        return result
        