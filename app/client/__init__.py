import os
from   baksys.utils             import *
from   baksys.backup            import *
from   baksys.event             import *
from   app.client.setting       import *
from   app.client.local_backup  import *
from   app.client.remote_backup import *
import app.com.console as console
    
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
        logger.error(e.message, e.error)
    
    def onBackupProgress(this, e):
        console.progressBar('%3d%%'%int(e.progress*100), e.progress)
        
    def onBackupError(this, e):
        print('\nerror when backup :', e.message, e.error)
        logger.error(e.message, e.error)
       
    def _loadCommands(this):
        this.commands['exit'] = { 'desc':'exit this program' }
        this.commands['help'] = { 'desc':'show help message', \
            'func':this.cmdHelp }
        this.commands['backup'] = { 'desc':'backup a folder or file', \
            'func':this.cmdBackup }
        this.commands['restore'] = { 'desc':'restore folder or file from a backup file', \
            'func':this.cmdRestore }
        this.commands['delete'] = { 'desc':'delete backup file', \
            'func':this.cmdDelete }
        this.commands['list'] = { 'desc':'list all avaiable backup file', \
            'func':this.cmdBackupList }
        # this.commands['sync']        = { 'desc':'synchronize local backups from remote backups', \
        #     'func':this.cmdSync }
        this.commands['remote-list'] = { 'desc':'update remote backups', \
            'func':this.cmdRemoteList }
        # this.commands['remote-upload'] = { 'desc':'update remote backups', \
        #     'func':this.cmdRemoteUpload }
        this.commands['remote-delete'] = { 'desc':'update remote backups', \
            'func':this.cmdRemoteDelete }
        # this.commands['remote-update'] = { 'desc':'update remote backups', \
        #     'func':this.cmdRemoteUpdate }
        
    def showBackupList(this, backupList):
        buffersize = os.get_terminal_size()
        fmt        = '%%-%ds %%-%ds %%%ds %%%ds' % (buffersize.columns-52, 25, 8, 15)
        backupPath = config['backup_path']
        
        print(fmt % ('backup', 'original path', 'CRC', 'size'))
        print('-'*(buffersize.columns-1))
        for item in backupList:
            size_display = {'G':0x40000000, 'M':0x100000, 'K':0x400, '':0}
            for tag in size_display:
                if item['size'] > size_display[tag]:
                    sizestr = '%d %sBytes' % (int(item['size']/size_display[tag]*100)/100, tag)
                    break
            print(fmt % (item['path'], item['origin_path'], '%08X' % item['crc'], sizestr))
        print()
            
    def checkRemoteConnection(this):
        try:
            if this.remoteBackup.isConnecting():
                return True
                
            address = input('remote address : ')
            if not this.remoteBackup.connect(address, BAKSYS_PORT):
                print('failed to connect server')
                return False
            
            username = input('username : ')
            password = input('password : ')
            if not this.remoteBackup.login(username, password):
                this.remoteBackup.disconnect()
                print('login failed')
                return False
                
            return True
        except KeyboardInterrupt:
            this.remoteBackup.disconnect()
            print()
        
    def cmdRemoteList(this):
        try:
            if not this.checkRemoteConnection(): return
            print('get list...')
            backupList = this.remoteBackup.getList()
            print('remote-list : \n')
            this.showBackupList(backupList)
        except Exception as e:
            logger.error('error on remote-list :', e)
            print('error on remote-list :', e)
        
    def cmdRemoteUpload(this):
        try:
            if not this.checkRemoteConnection(): return
        except Exception as e:
            logger.error('error on remote-upload :', e)
            print('error on remote-upload :', e)
        
    def cmdRemoteDelete(this):
        try:
            if not this.checkRemoteConnection():
                return
            path = input('remote backup : ')
            result = this.remoteBackup.deleteBackup(path)
            if result:
                print('delete finish.')
        except Exception as e:
            logger.error('error on remote-delete :', e)
            print('error on remote-delete :', e)
            
    def cmdRemoteUpdate(this):
        try:
            if not this.checkRemoteConnection(): return
            print('get update list...')
            updateList     = this.remoteBackup.getUpdateList(this.localBackup.getList())
            totalCount     = len(updateList)
            completedCount = 0
            print('%d backup need to update.' % totalCount)
            print('start update remote backup files...')
            this.remoteBackup.updateRemote(updateList)
        except Exception as e:
            logger.error('error on remote-update :', e)
            print('error on remote-update :', e)
    # end cmdUpdate
    
    def cmdDelete(this):
        name      = input('name of backup: ')
        print('backup \'%s\' was deleted' % name)
        
    def cmdBackupList(this):
        print('backup-list : \n')
        this.showBackupList(this.localBackup.getList())
        
    def cmdBackup(this):
        path     = input('path you want to backup: ')
        name     = input('name of backup: ')
        override = False
        
        backupPath = config['backup_path']
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
                    saveConfig()
                    print('see you~')
                    break
                elif cmd in this.commands:
                    this.commands[cmd]['func']()
                else:
                    print('can\'t find command \'%s\'' % cmd)
            except KeyboardInterrupt:
                print('^C')
# end BaksysClientApp