import os
import shutil
import tempfile
import baksys.config as config
from   baksys.backup      import *
from   baksys.event       import *
from   app.client.setting import *

class BaksysLocalBackup:
    def __init__(this):
        this.backupPath        = config.get('backup_path')
        
        this.onBackupFailed    = BaksysEvent()
        this.onBackupProgress  = BaksysEvent()
        this.onBackupFinished  = BaksysEvent()
        
        this.onRestoreFailed   = BaksysEvent()
        this.onRestoreProgress = BaksysEvent()
        this.onRestoreFinished = BaksysEvent()
        
    def getBackup(path):
        backupDir  = config.get('backup_path')
        backupFile = os.path.join(backupDir, path)
        
        if not os.path.exists(backupFile):
            return None
        
        backup = BaksysBackup()
        backup.load(backupFile)
        return backup
        
    # restore backup
    def restore(this, backup, path, **option):
        override = BaksysUtils.loadOption(option, 'override', False)
        totalFileCount    = 0
        totalDirCount     = 0
        finishedFileCount = 0
        finishedDirCount  = 0
        
        # calculate total file count and directory count
        backupItems = [backup.pData]
        while backupItems:
            item = backupItems.pop()
            if item.nType == BaksysItemType.Directory:
                for subitem in item.aItems:
                    backupItems.insert(0, subitem)
                totalDirCount  += 1
            else:
                totalFileCount += 1
        
        # make non-existed directories
        if not os.path.exists(path):
            os.makedirs(path)
            
        try:
            backupItems = [{ 'item':backup.pData, 'path':path }]
            
            # create directory and extract file
            while backupItems:
                obj      = backupItems.pop()
                fullpath = os.path.join(obj['path'], obj['item'].sName)
                if obj['item'].nType == BaksysItemType.Directory:
                    if not os.path.exists(fullpath):
                        os.makedirs(fullpath)
                    for subitem in obj['item'].aItems:
                        backupItems.insert(0, { 'item':subitem, 'path':fullpath })
                    finishedDirCount += 1
                else:
                    obj['item'].extract(obj['path'], override = override)
                    finishedFileCount += 1
                
                # invoke progress event
                eventArgs = BaksysEventArgs()
                eventArgs.progress = finishedFileCount/totalFileCount
                this.onRestoreProgress.invoke(eventArgs)
            
            # invoke finished event
            eventArgs = BaksysEventArgs()
            eventArgs.message = ((\
                'restore finish.\n'  +  \
                'path        : %s\n' +  \
                'directories : %d\n' +  \
                'files       : %d') % ( \
                path,                   \
                totalDirCount,          \
                totalFileCount ))
            this.onRestoreFinished.invoke(eventArgs)
        except KeyboardInterrupt:
            eventArgs = BaksysEventArgs()
            eventArgs.message = 'restore was interrupted.'
            eventArgs.error   = e
            this.onRestoreFailed.invoke(eventArgs)
        except (Exception, BaseException) as e:
            eventArgs = BaksysEventArgs()
            eventArgs.message = 'restore failed.'
            eventArgs.error   = e
            this.onRestoreFailed.invoke(eventArgs)
    # end restore
        
    # backup specific directory or file
    def backup(this, name, path, **option):  
        source     = os.path.abspath(os.path.dirname(path))
        target     = os.path.basename(path)
        override   = BaksysUtils.loadOption(option, 'override', False)
        backupFile = os.path.join(this.backupPath, name)
        
        if os.path.exists(backupFile) and not override:
            eventArgs = BaksysEventArgs()
            eventArgs.message = 'file \'%s\' has existed.' % path
            eventArgs.error   = None
            this.onBackupFailed.invoke(eventArgs)
            return
            
        if not os.path.exists(path):
            eventArgs = BaksysEventArgs()
            eventArgs.message = 'file or directory is not found. path : \'%s\'' % path
            eventArgs.error   = None
            this.onBackupFailed.invoke(eventArgs)
            return
        
        try:
            this.backupState  = { \
                'totalFileCount'    : 0,\
                'totalDirCount'     : 0,\
                'finishedFileCount' : 0,\
                'finishedDirCount'  : 0 \
            }
            temppath = os.path.join(BAKSYS_TEMPDIR, 'tmp_'+os.path.basename(path))
                
            backup = BaksysBackup()
            backup.sPath = source
            backup.pData = this._loadBackupItem(backup, target, source)
            backup.onProgress += this._BackupFile_Progress
            
            # calculate total file count and directory count
            backupItems = [backup.pData]
            while backupItems:
                item = backupItems.pop()
                if item.nType == BaksysItemType.Directory:
                    for subitem in item.aItems:
                        backupItems.insert(0, subitem)
                    this.backupState['totalDirCount']  += 1
                else:
                    this.backupState['totalFileCount'] += 1
            
            backup.save(temppath, override = override)
            # move temp file 
            if os.path.exists(backupFile):
                os.remove(backupFile)
            shutil.move(temppath, backupFile)
            
            # invoke finished event
            eventArgs = BaksysEventArgs()
            eventArgs.message = (\
                '\'%s\' backup finished. \n' +     \
                'backup     : \'%s\' \n' +         \
                'directories: %d \n' +             \
                'files      : %d') % (             \
                os.path.join(source, target),      \
                name,                              \
                this.backupState['totalDirCount'], \
                this.backupState['totalFileCount'])
            this.onBackupFinished.invoke(eventArgs)
        except KeyboardInterrupt as e:
            if os.path.exists(temppath): 
                os.remove(temppath)
            eventArgs = BaksysEventArgs()
            eventArgs.message = 'backup was interrupted.'
            eventArgs.error   = e
            this.onBackupFailed.invoke(eventArgs)
        except (Exception, BaseException) as e:
            if os.path.exists(temppath): 
                os.remove(temppath)
            eventArgs = BaksysEventArgs()
            eventArgs.message = 'backup failed.'
            eventArgs.error   = e
            this.onBackupFailed.invoke(eventArgs)
    # end backup
    
    def _loadBackupItem(this, pkg, path, base):
        name     = os.path.basename(path)
        fullPath = os.path.join(base, path)
        
        if os.path.isdir(fullPath):
            item     = BaksysDirectory(name)
            dirItems = os.listdir(fullPath)
            for itemName in dirItems:
                itemPath = os.path.join(path, itemName)
                subItem  = this._loadBackupItem(pkg, itemPath, base)
                item.aItems.append(subItem)
        else:
            item = BaksysFile(name, fullPath)
            
        item.pkg = pkg
        return item
    
    def _BackupFile_Progress(this, e):
        if e.item.nType == BaksysItemType.Directory:
            this.backupState['finishedDirCount'] += 1
        else:
            this.backupState['finishedFileCount'] += 1
            
        eventArgs = BaksysEventArgs()
        eventArgs.progress = this.backupState['finishedFileCount'] / this.backupState['totalFileCount']
        this.onBackupProgress.invoke(eventArgs)
        
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
        