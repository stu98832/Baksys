import threading
import app.com.packet        as packet
import app.com.packet.backup
from   app.server.setting     import *
from   app.server.user_backup import *

BAKSYS_ROOT_USERNAME = 'root'
BAKSYS_ROOT_PASSWORD = '12345678'

def handleLogin(client, username, password):
    success = username == BAKSYS_ROOT_USERNAME and password == BAKSYS_ROOT_PASSWORD
    
    if success:
        client.login    = True
        client.username = username
        client.backup   = BaksysUserBackup(username)
    
    client.socket.send(packet.operationResponse(success))
# end handleLogin
    
def handleBackupRequest(client, message):
    subtype = message.readByte()
    if   subtype == packet.backup.REQUEST_TYPE_LIST:
        backupList = client.backup.getList()
        client.socket.send(packet.backup.listResponse(backupList))
    # end REQUEST_TYPE_LIST
    elif subtype == packet.backup.REQUEST_TYPE_DELETE:
        deletePath = message.readString()
        try:
            client.backup.deleteBackup(deletePath)
            client.socket.send(packet.operationResponse(True))
        except RuntimeError as e:
            client.socket.send(packet.operationResponse(False, str(e)))
        except Exception as e:
            logger.error('error on delete backup', e)
            client.socket.send(packet.operationResponse(False, 'internal error'))
    # end REQUEST_TYPE_DELETE
    elif subtype == packet.backup.REQUEST_TYPE_UPDATE_LIST:
        count = message.readInt()
        remoteList = []
        updateList = []
        backupList = client.backup.getList()
        
        for i in range(count):
            path = message.readString()
            crc  = message.readUInt()
            remoteList.append({'path':path, 'crc':crc})
            
        for remoteItem in remoteList:
            sameBackup = False
            for backupItem in backupList:
                if  backupItem['path'] == remoteItem['path'] and \
                    backupItem['crc']  == remoteItem['crc']:
                    sameBackup = True
                    break
            if not sameBackup:
                updateList.append(remoteItem)
        client.socket.send(packet.backup.updateListResponse(updateList))
    # end REQUEST_TYPE_UPDATE_LIST
# end handleBackupRequest
            
def handleDownloadRequest(client, message):
    subtype = message.readByte()
    if   subtype == packet.backup.UPLOAD_DOWNLOAD_START:
        downloadPath = message.readString()
        try:
            client.backup.startUpload(client, downloadPath)
        except RuntimeError as e:
            client.socket.send(packet.operationResponse(False, str(e)))
        except Exception as e:
            logger.error('error on delete backup', e)
            client.socket.send(packet.operationResponse(False, 'internal error'))
    # end UPLOAD_DOWNLOAD_START
    elif subtype == packet.backup.UPLOAD_DOWNLOAD_BREAK:
        client.backup.uploadInterrupted = True
    # end UPLOAD_DOWNLOAD_BREAK
# end handleDownloadRequest
    

def handleUploadRequest(client, message):
    subtype = message.readByte()
    if subtype == packet.backup.UPLOAD_DOWNLOAD_START:
        downloadPath = message.readString()
        try:
            client.backup.acceptUpload(downloadPath)
            client.socket.send(packet.operationResponse(True))
        except RuntimeError as e:
            client.socket.send(packet.operationResponse(False, str(e)))
        except Exception as e:
            logger.error('error on start accept upload', e)
            client.socket.send(packet.operationResponse(False, str(e)))
    # end UPLOAD_DOWNLOAD_START
    elif subtype == packet.backup.UPLOAD_DOWNLOAD_BREAK:
        client.backup.acceptUploadInterrutpt()
    # end UPLOAD_DOWNLOAD_BREAK
    elif subtype == packet.backup.UPLOAD_DOWNLOAD_CONTINUE:
        offset = message.readLong()
        size   = message.readLong()
        data   = message.readBuffer(size)
        try:
            client.backup.acceptUploadData(offset, data)
        except RuntimeError as e:
            client.backup.acceptUploadInterrutpt()
        except Exception as e:
            logger.error('error on start accept upload data', e)
            client.backup.acceptUploadInterrutpt()
            
    # end UPLOAD_DOWNLOAD_CONTINUE
    elif subtype == packet.backup.UPLOAD_DOWNLOAD_FINISH:
        try:
            client.backup.acceptUploadFinish()
            client.socket.send(packet.operationResponse(True))
        except RuntimeError as e:
            client.socket.send(packet.operationResponse(False, str(e)))
        except Exception as e:
            logger.error('error on start finish upload accept', e)
            client.socket.send(packet.operationResponse(False, str(e)))
    # end UPLOAD_DOWNLOAD_FINISH
# end handleUploadRequest
