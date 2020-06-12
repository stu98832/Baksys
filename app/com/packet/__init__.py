from baksys.io import *

REQUEST_LOGIN      = 0x01
REQUEST_BACKUP     = 0x02
REQUEST_UPLOAD     = 0x03
REQUEST_DOWNLOAD   = 0x04

RESPONSE_OPERATION = 0x01
RESPONSE_BACKUP    = 0x02

def operationResponse(success, reason = ''):
    packet = BaksysMemoryStream()
    writer = BaksysBinaryWriter(packet)
    writer.writeByte(RESPONSE_OPERATION)
    writer.writeByte(1 if success else 0)
    if not success:
        writer.writeString(reason)
    print(packet.getBuffer())
    return packet.getBuffer()