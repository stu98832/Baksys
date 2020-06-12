from baksys.io      import *
from app.com.packet import *
        
def loginRequest(username, password):
    packet = BaksysMemoryStream()
    writer = BaksysBinaryWriter(packet)
    writer.writeByte(REQUEST_LOGIN)
    writer.writeString(username)
    writer.writeString(password)
    return packet.getBuffer()