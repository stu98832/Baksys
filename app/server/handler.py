import app.com.packet as packet
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
    client.socket.send(packet.loginResponse(success))
    
def handleListRequest(client):
    backupList = client.backup.getList()
    client.socket.send(packet.backupListResponse(backupList))
    
def handleDeleteRequest(client, path):
    try:
        client.backup.deleteBackup(path)
        client.socket.send(packet.backupDeleteResponse(True))
    except Exception as e:
        client.socket.send(packet.backupDeleteResponse(False, str(e)))