import os
import shutil
import threading
import time
from   baksys.backup         import *
from   baksys.event          import *
from   app.server.setting    import *
import app.com.packet.backup as backupPacket

class BaksysUserBackup:
    def __init__(this, username):
        this.backupPath = os.path.join(config['backup_path'], username)
        this.uploadThread = None
        if not os.path.exists(this.backupPath):
            os.makedirs(this.backupPath)
        
    def _checkPathValid(this, path):
        if '..' in path:
            raise RuntimeError('unsafe path \'%s\' denied!' % path)
            
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
                    client.socket.send(backupPacket.downloadStartResponse(size))
                    while size > 0:
                        if this.downloadInterrupted:
                            client.socket.send(backupPacket.downloadBreakResponse())
                            return
                        sizeToWrite = min(8192, size)
                        data        = file.read(sizeToWrite)
                        client.socket.send(backupPacket.downloadDataResponse(offset, data))
                        offset += sizeToWrite
                        size   -= sizeToWrite
                client.socket.send(backupPacket.downloadFinishResponse())
            except Exception as e:
                client.socket.send(backupPacket.downloadBreakResponse())
        
        this.downloadInterrupted = False
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
        