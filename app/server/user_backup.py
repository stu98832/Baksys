import os
import shutil
import tempfile
import baksys.config as config
from   baksys.backup      import *
from   baksys.event       import *

class BaksysUserBackup:
    def __init__(this, username):
        this.backupPath = os.path.join(config.get('backup_path'), username)
        if not os.path.exists(this.backupPath):
            os.makedirs(this.backupPath)
        
    def _checkPathValid(this, path):
        if '..' in path:
            raise RuntimeError('unsafe path \'%s\' denied!' % path)
        
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
                    
        return result
        