from baksys.io import *

BAKSYS_LOGIN_REQUEST        = 0x01
BAKSYS_UPDATE_LIST_REQUEST  = 0x02
BAKSYS_UPLOAD_REQUEST       = 0x03

BAKSYS_LOGIN_RESPONSE       = 0x01
BAKSYS_UPDATE_LIST_RESPONSE = 0x02
BAKSYS_UPLOAD_RESPONSE      = 0x03
        
def loginRequest(username, password):
    packet = BaksysMemoryStream()
    writer = BaksysBinaryWriter(packet)
    writer.writeByte(BAKSYS_LOGIN_REQUEST)
    writer.writeString(username)
    writer.writeString(password)
    return packet.getBuffer()

def loginResponse(success):
    packet = BaksysMemoryStream()
    writer  = BaksysBinaryWriter(packet)
    writer.writeByte(BAKSYS_LOGIN_RESPONSE)
    writer.writeByte(1 if success else 0)
    return packet.getBuffer()

def updateListRequest(backupList):
    packet = BaksysMemoryStream()
    writer = BaksysBinaryWriter(packet)
    writer.writeByte(BAKSYS_UPDATE_LIST_REQUEST)
    writer.writeEncodingInt(len(backupList))
    for item in backupList:
        writer.writeString(item['path'])
        writer.writeUInt(item['crc'])
    return packet.getBuffer()
    
def updateListResponse(updateList):
    packet = BaksysMemoryStream()
    writer = BaksysBinaryWriter(packet)
    writer.writeByte(BAKSYS_UPDATE_LIST_REQUEST)
    writer.writeEncodingInt(len(updateList))
    for item in updateList:
        writer.writeString(item['path'])
    return packet.getBuffer()