import os
import baksys.config as config
from   baksys.utils             import *
from   baksys.backup            import *
from   baksys.event             import *
from   app.client.setting       import *
from   app.client.local_backup  import *
from   app.client.remote_backup import *
import app.com.console as console
import app.com.log
    
class BaksysClientApp:
    def __init__(this):
        this.commands = { }
        this._loadCommands()
        this.localBackup = BaksysLocalBackup()
        this.localBackup.onRestoreFailed   += this.onRestoreError
        this.localBackup.onRestoreProgress += this.onRestoreProgress
        this.localBackup.onRestoreFinished += lambda e: print('\n'+e.message)
        this.localBackup.onBackupFailed    += this.onBackupError
        this.localBackup.onBackupProgress  += this.onBackupProgress
        this.localBackup.onBackupFinished  += lambda e: print('\n'+e.message)
        this.remoteBackup = BaksysRemoteBackup()
    
    # events
    def onRestoreProgress(this, e):
        console.progressBar('%3d%%'%int(e.progress*100), e.progress)
        
    def onRestoreError(this, e):
        print('\nerror when restore :', e.message, e.error)
        app.com.log.error(e.message, e.error)
    
    def onBackupProgress(this, e):
        console.progressBar('%3d%%'%int(e.progress*100), e.progress)
        
    def onBackupError(this, e):
        print('\nerror when backup :', e.message, e.error)
        app.com.log.error(e.message, e.error)
       
    def _loadCommands(this):
        this.commands['exit']    = { 'desc':'exit this program' }
        this.commands['help']    = { 'desc':'show help message', \
            'func':this.cmdHelp }
        this.commands['backup']  = { 'desc':'backup a folder or file', \
            'func':this.cmdBackup }
        this.commands['restore'] = { 'desc':'restore folder or file from a backup file', \
            'func':this.cmdRestore }
        this.commands['delete']  = { 'desc':'delete backup file', \
            'func':this.cmdDelete }
        this.commands['list']    = { 'desc':'list all avaiable backup file', \
            'func':this.cmdBackupList }
        # this.commands['sync']        = { 'desc':'synchronize local backups from remote backups', \
        #     'func':this.cmdSync }
        this.commands['update']      = { 'desc':'update remote backups', \
            'func':this.cmdUpdate }
    
    def cmdUpdate(this):
        try:
            address = input('remote address : ')
            if not this.remoteBackup.connect(address, BAKSYS_PORT):
                print('failed to connect server')
                return
            
            username = input('username : ')
            password = input('password : ')
            if not this.remoteBackup.login(username, password):
                print('login failed')
                return
            
            print('get update list...')
            updateList     = this.remoteBackup.getUpdateList(this.localBackup.getList())
            totalCount     = len(updateList)
            completedCount = 0
            print('%d backup need to update.' % totalCount)
            print('start update remote backup files...')
            for itempath in updateList:
                this.sendUpdateBackupRequest()
                completedCount += 1 if this.waitForResponse() else 0
                this.showProgressBar('%d/%d' % (completedCount, totalCount), completedCount/totalCount)
            
            if totalCount == completedCount:
                print('\nupdate finished')
            else:
                print('\nupdate failed. %d items update failed' % (totalCount-completedCount))
        except Exception as e:
            app.com.log.error('error on update :', e)
            print('error on update :', e)
    # end cmdUpdate
    
    def cmdDelete(this):
        name      = input('name of backup: ')
        backupDir = config.get('backup_path')
        fullpath  = os.path.join(backupDir, name)
        
        if not os.path.exists(fullpath):
            print('can\'t find backup file \'%s\' at \'%s\'' % (name, backupDir))
            return
            
        os.remove(fullpath)
        print('backup \'%s\' was deleted' % name)
        
    def cmdBackupList(this):
        buffersize = os.get_terminal_size()
        fmt        = '%%-%ds %%-%ds %%%ds %%%ds' % (buffersize.columns-67, 40, 8, 15)
        backupPath = config.get('backup_path')
        
        print(fmt % ('backup', 'original path', 'CRC', 'size'))
        print('-'*(buffersize.columns-1))
        for item in this.localBackup.getList():
            size_display = {'G':0x40000000, 'M':0x100000, 'K':0x400, '':0}
            for tag in size_display:
                if item['size'] > size_display[tag]:
                    sizestr = '%d %sBytes' % (int(item['size']/size_display[tag]*100)/100, tag)
                    break
            print(fmt % (item['path'], item['origin_path'], '%08X' % item['crc'], sizestr))
        
    def cmdBackup(this):
        path     = input('path you want to backup: ')
        name     = input('name of backup: ')
        override = False
        
        backupPath = config.get('backup_path')
        if os.path.exists(os.path.join(backupPath, name)):
            override = console.askYesNo('backup \'%s\' has existed, are you want to override?' % name)
            if not override:
                print('cancel backup.')
                return
                
        print('start backup')
        this.localBackup.backup(name, path, override=override)
        
    def cmdRestore(this):
        name = input('name of backup: ')
        
        backup = this.localBackup.getBackup(name)
        
        if backup == None:
            print('can\'t find backup file \'%s\'' % name)
            return
        
        path     = backup.sPath
        override = False
        if not console.askYesNo('use default path\'%s\'?' % path):
            path = input('new restore path : ')
            
        if os.path.exists(path):
            if not os.path.isdir(path):
                print('can\'t restore on a file!')
                return 
            elif len(os.listdir(path)) > 0:
                override = console.askYesNo('directory \'%s\' is not empty, are you want to override?')
        
        print('start restore')
        this.localBackup.restore(backup, path, override = override)
        
    def cmdHelp(this):
        maxlen = 0
        for cmd in this.commands:
            maxlen = max(maxlen, len(cmd))
            
        fmt = '%%-%ds : %%s' % (maxlen)
        for cmd in this.commands:
            print(fmt % (cmd, this.commands[cmd]['desc']))

    # baksys command line
    def run(this):
        print('\'help\' to show help message')
        while True:
            try:
                cmd = input('> ')
                
                if cmd == 'exit':
                    config.save(BAKSYS_CONFIG)
                    print('see you~')
                    break
                elif cmd in this.commands:
                    this.commands[cmd]['func']()
                else:
                    print('can\'t find command \'%s\'' % cmd)
            except KeyboardInterrupt:
                print('^C')
# end BaksysClientApp