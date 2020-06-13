import os
import sys
import time
from   app.client         import BaksysClientApp
from   app.client.setting import *

scriptList = {}

def initScript():
    global scriptList
    scriptList = { \
        'help'   : {'func':scriptHelp  , 'usage':'help'}, \
        'backup' : {'func':scriptBackup, 'usage':'backup {source path} {backup name} [--override]'}, \
        'update' : {'func':scriptUpdate, 'usage':'update {address} {username} {password}'}, \
    }
    
def scriptHelp(*trunk):
    for command in scriptList:
        print('%s:\n[usage] %s' % (command, scriptList[command]['usage']))
    
def scriptBackup(srcPath, backupPath, *option):
    if not os.path.exists(srcPath):
        scriptLogger.error('script-backup : non-existed path \'%s\'' % srcPath)
        print('non-existed path \'%s\'' % srcPath)
        return

    client = BaksysClientApp()
    client.localBackup.onBackupFailed += lambda e: \
        scriptLogger.error('script-backup : %s' % e.message, e.error)
    os.path.join(backupPath, time.strftime('%Y-%m-%d_%H_%M_%S', time.localtime()))
    client.localBackup.backup(backupPath, srcPath, override=('--override' in option))
    
def scriptUpdate(address, username, password, *trunk):
    client = BaksysClientApp()
    finishedCount = 0
    totalCount    = 0
    try:
        if not client.remoteBackup.connect(address, BAKSYS_PORT):
            scriptLogger.error('script-update failed : can\' connect to %s:%s' % (address, BAKSYS_PORT))
            return
        if not client.remoteBackup.login(username, password):
            client.remoteBackup.disconnect()
            scriptLogger.error('script-update failed : can\' login user \'%s\'' % username)
            return
        updateList    = client.remoteBackup.getUpdateList(client.localBackup.getList())
        totalCount    = len(updateList)
        for itemPath in updateList:
            result = client.remoteBackup.startUpload(itemPath)
            if not result:
                scriptLogger.error('script-update(%d/%d)[%s]' % \
                    (finishedCount+1, totalCount, itemPath), \
                    client.remoteBackup.lastOperationError)
            result = client.remoteBackup.getUploadResult()
            if not result:
                scriptLogger.error('script-update(%d/%d)[%s]' % \
                    (finishedCount+1, totalCount, itemPath), \
                    client.remoteBackup.lastOperationError)
                return
            finishedCount += 1
    except Exception as e:
        logger.error('script-update(%d/%d)[%s]' % \
            (finishedCount+1, totalCount, itemPath), \
            e)
    
def main():
    initScript()
    command = sys.argv[1]  if len(sys.argv) > 1 else 'help'
    params  = sys.argv[2:] if len(sys.argv) > 2 else []
    if command not in scriptList:
        print('invalid command \'%s\'' % command)
        command = 'help'
    try:
        scriptList[command]['func'](*params)
    except TypeError as e:
        print(e)
        print(scriptList[command]['usage'])

main()