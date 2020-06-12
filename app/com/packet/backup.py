from baksys.io      import *
from app.com.packet import *

REQUEST_TYPE_LIST        = 0x01
REQUEST_TYPE_DELETE      = 0x02
REQUEST_TYPE_UPDATE_LIST = 0x03
    
def listRequest():
    packet = BaksysMemoryStream()
    writer = BaksysBinaryWriter(packet)
    writer.writeByte(REQUEST_BACKUP)
    writer.writeByte(REQUEST_TYPE_LIST)
    return packet.getBuffer()
    
def listResponse(backupList):
    packet = BaksysMemoryStream()
    writer = BaksysBinaryWriter(packet)
    writer.writeByte(RESPONSE_BACKUP)
    writer.writeByte(REQUEST_TYPE_LIST)
    writer.writeEncodingInt(len(backupList))
    for item in backupList:
        writer.writeString(item['path'])
        writer.writeString(item['origin_path'])
        writer.writeLong(item['size'])
        writer.writeUInt(item['crc'])
    return packet.getBuffer()
    
def deleteRequest(path):
    packet = BaksysMemoryStream()
    writer = BaksysBinaryWriter(packet)
    writer.writeByte(REQUEST_BACKUP)
    writer.writeByte(REQUEST_TYPE_DELETE)
    writer.writeString(path)
    return packet.getBuffer()

def updateListRequest(backupList):
    packet = BaksysMemoryStream()
    writer = BaksysBinaryWriter(packet)
    writer.writeByte(REQUEST_BACKUP)
    writer.writeByte(REQUEST_TYPE_UPDATE_LIST)
    writer.writeEncodingInt(len(backupList))
    for item in backupList:
        writer.writeString(item['path'])
        writer.writeUInt(item['crc'])
    return packet.getBuffer()
    
def updateListResponse(updateList):
    packet = BaksysMemoryStream()
    writer = BaksysBinaryWriter(packet)
    writer.writeByte(RESPONSE_BACKUP)
    writer.writeByte(REQUEST_TYPE_UPDATE_LIST)
    writer.writeEncodingInt(len(updateList))
    for item in updateList:
        writer.writeString(item['path'])
    return packet.getBuffer()
    
UPLOAD_DOWNLOAD_START    = 0x01
UPLOAD_DOWNLOAD_CONTINUE = 0x02
UPLOAD_DOWNLOAD_FINISH   = 0x03
UPLOAD_DOWNLOAD_BREAK    = 0x04

def downloadRequest(remotePath):
    packet = BaksysMemoryStream()
    writer = BaksysBinaryWriter(packet)
    writer.writeByte(REQUEST_DOWNLOAD)
    writer.writeByte(UPLOAD_DOWNLOAD_START)
    writer.writeString(remotePath)
    return packet.getBuffer()
    
def downloadBreakRequest():
    packet = BaksysMemoryStream()
    writer = BaksysBinaryWriter(packet)
    writer.writeByte(REQUEST_DOWNLOAD)
    writer.writeByte(UPLOAD_DOWNLOAD_BREAK)
    return packet.getBuffer()
    
def downloadBreakResponse():
    packet = BaksysMemoryStream()
    writer = BaksysBinaryWriter(packet)
    writer.writeByte(RESPONSE_DOWNLOAD)
    writer.writeByte(UPLOAD_DOWNLOAD_BREAK)
    return packet.getBuffer()

def downloadDataResponse(offset, data):
    packet = BaksysMemoryStream()
    writer = BaksysBinaryWriter(packet)
    writer.writeByte(RESPONSE_DOWNLOAD)
    writer.writeByte(UPLOAD_DOWNLOAD_CONTINUE)
    writer.writeLong(offset)
    writer.writeLong(len(data))
    writer.writeBuffer(data)
    return packet.getBuffer()
    
def downloadFinishResponse():
    packet = BaksysMemoryStream()
    writer = BaksysBinaryWriter(packet)
    writer.writeByte(RESPONSE_DOWNLOAD)
    writer.writeByte(UPLOAD_DOWNLOAD_FINISH)
    return packet.getBuffer()
    
def downloadStartResponse(size):
    packet = BaksysMemoryStream()
    writer = BaksysBinaryWriter(packet)
    writer.writeByte(RESPONSE_DOWNLOAD)
    writer.writeByte(UPLOAD_DOWNLOAD_START)
    writer.writeLong(size)
    return packet.getBuffer()
    