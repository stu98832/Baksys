import threading
import app.com.packet        as packet
import app.com.packet.backup
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
    elif subtype == packet.backup.REQUEST_TYPE_DELETE:
        deletePath = message.readString()
        try:
            client.backup.deleteBackup(deletePath)
            client.socket.send(packet.operationResponse(True))
        except Exception as e:
            client.socket.send(packet.operationResponse(False, str(e)))
# end handleBackupRequest
            
def handleDownloadRequest(client, message):
    subtype = message.readByte()
    if subtype == packet.backup.UPLOAD_DOWNLOAD_START:
        downloadPath = message.readString()
        try:
            client.backup.startUpload(client, downloadPath)
        except Exception as e:
            client.socket.send(packet.operationResponse(False, str(e)))
    if subtype == packet.backup.UPLOAD_DOWNLOAD_BREAK:
# end handleDownloadRequest
    