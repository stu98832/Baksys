import app.com.packet        as packet
import app.com.packet.login  as loginPacket
import app.com.packet.backup as backupPacket
from   app.server.user_backup import *

BAKSYS_ROOT_USERNAME = 'root'
BAKSYS_ROOT_PASSWORD = '12345678'

def handleLogin(client, username, password):
    success = username == BAKSYS_ROOT_USERNAME and password == BAKSYS_ROOT_PASSWORD
    
    if success:
        client.login    = True
        client.username = username
        client.backup   = BaksysUserBackup(username)
    
    # send response packet
    client.socket.send(packet.operationResponse(success))
    
def handleBackupRequest(client, message):
    subtype = message.readByte()
    if   subtype == backupPacket.REQUEST_TYPE_LIST:
        backupList = client.backup.getList()
        client.socket.send(backupPacket.listResponse(backupList))
    elif subtype == backupPacket.REQUEST_TYPE_DELETE:
        deletePath = message.readString()
        try:
            client.backup.deleteBackup(deletePath)
            client.socket.send(packet.operationResponse(True))
        except Exception as e:
            client.socket.send(packet.operationResponse(False, str(e)))