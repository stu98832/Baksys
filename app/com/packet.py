from baksys.io import *

BAKSYS_LOGIN_REQUEST           = 0x01
BAKSYS_LIST_REQUEST            = 0x02
BAKSYS_UPLOAD_START_REQUEST    = 0x03
BAKSYS_UPLOAD_CONTINUE_REQUEST = 0x04
BAKSYS_UPLOAD_FINISH_REQUEST   = 0x05
BAKSYS_DELETE_REQUEST          = 0x06
BAKSYS_UPDATE_LIST_REQUEST     = 0x07

BAKSYS_LOGIN_RESPONSE           = 0x01
BAKSYS_LIST_RESPONSE            = 0x02
BAKSYS_UPLOAD_START_RESPONSE    = 0x03
BAKSYS_UPLOAD_CONTINUE_RESPONSE = 0x04
BAKSYS_UPLOAD_FINISH_RESPONSE   = 0x05
BAKSYS_DELETE_RESPONSE          = 0x06
BAKSYS_UPDATE_LIST_RESPONSE     = 0x07
        
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
    
def backupListRequest():
    packet = BaksysMemoryStream()
    writer = BaksysBinaryWriter(packet)
    writer.writeByte(BAKSYS_LIST_REQUEST)
    return packet.getBuffer()
    
def backupListResponse(backupList):
    packet = BaksysMemoryStream()
    writer = BaksysBinaryWriter(packet)
    writer.writeByte(BAKSYS_LIST_RESPONSE)
    writer.writeEncodingInt(len(backupList))
    for item in backupList:
        writer.writeString(item['path'])
        writer.writeString(item['origin_path'])
        writer.writeLong(item['size'])
        writer.writeUInt(item['crc'])
    return packet.getBuffer()
    
def backupUploadStartRequest(path):
    packet = BaksysMemoryStream()
    writer = BaksysBinaryWriter(packet)
    writer.writeByte(BAKSYS_UPLOAD_START_REQUEST)
    writer.writeString(path)
    return packet.getBuffer()
    
def backupUploadStartResponse(success, reason = ''):
    packet = BaksysMemoryStream()
    writer = BaksysBinaryWriter(packet)
    writer.writeByte(BAKSYS_UPLOAD_START_RESPONSE)
    writer.writeByte(1 if success else 0)
    if not success:
        writer.writeString(reason)
    return packet.getBuffer()
    
def backupUploadContinueRequest(offset, data):
    packet = BaksysMemoryStream()
    writer = BaksysBinaryWriter(packet)
    writer.writeByte(BAKSYS_UPLOAD_CONTINUE_REQUEST)
    writer.writeEncodingInt(offset)
    writer.writeEncodingInt(len(data))
    writer.writeBuffer(data)
    return packet.getBuffer()
    
def backupUploadContinueResponse(success, reason = ''):
    packet = BaksysMemoryStream()
    writer = BaksysBinaryWriter(packet)
    writer.writeByte(BAKSYS_UPLOAD_CONTINUE_RESPONSE)
    writer.writeByte(1 if success else 0)
    if not success:
        writer.writeString(reason)
    return packet.getBuffer()
    
def backupUploadFinishRequest():
    packet = BaksysMemoryStream()
    writer = BaksysBinaryWriter(packet)
    writer.writeByte(BAKSYS_UPLOAD_FINISH_REQUEST)
    return packet.getBuffer()
    
def backupUploadFinishResponse(success, reason = ''):
    packet = BaksysMemoryStream()
    writer = BaksysBinaryWriter(packet)
    writer.writeByte(BAKSYS_UPLOAD_FINISH_RESPONSE)
    writer.writeByte(1 if success else 0)
    if not success:
        writer.writeString(reason)
    return packet.getBuffer()
    
def backupDeleteRequest(path):
    packet = BaksysMemoryStream()
    writer = BaksysBinaryWriter(packet)
    writer.writeByte(BAKSYS_DELETE_REQUEST)
    writer.writeString(path)
    return packet.getBuffer()
    
def backupDeleteResponse(success, reason = ''):
    packet = BaksysMemoryStream()
    writer = BaksysBinaryWriter(packet)
    writer.writeByte(BAKSYS_DELETE_RESPONSE)
    writer.writeByte(1 if success else 0)
    if not success:
        writer.writeString(reason)
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
    writer.writeByte(BAKSYS_UPDATE_LIST_RESPONSE)
    writer.writeEncodingInt(len(updateList))
    for item in updateList:
        writer.writeString(item['path'])
    return packet.getBuffer()