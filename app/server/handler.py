import baksys.config  as config
import app.com.packet as packet

BAKSYS_ROOT_USERNAME = 'root'
BAKSYS_ROOT_PASSWORD = '12345678'

def handleLogin(client, username, password):
    success = username == BAKSYS_ROOT_USERNAME and password == BAKSYS_ROOT_PASSWORD
    
    if success:
        client.login    = True
        client.username = username
    
    # send response packet
    client.socket.send(packet.loginResponse(success))