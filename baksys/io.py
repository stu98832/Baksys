import struct
from baksys.utils import BaksysUtils

class BaksysMemoryStream:
    def __init__(this, buffer = []):
        this._buffer   = list(buffer)
        this._position = 0
        this._flushed  = False
        this._closed   = False
        
    def __del__(this):
        this.close()
        
    def length(this):
        return len(this._buffer)
        
    def position(this):
        return this._position
        
    def write(this, buffer:bytes):
        assert not this._closed , 'can\'t read with a closed stream'
        assert not this._flushed, 'can\'t read with a flushed stream'
        
        count      = len(buffer)
        over_count = this.length() - this._position
        for i in range(0, over_count):
            this._buffer[this._position + i] = buffer[i]
        
        this._buffer.extend(buffer[over_count:])
        this._position += count
        
    def read(this, size:int):
        assert not this._closed, 'can\'t read with a closed stream'
        assert size >= 0, 'negative size'
        
        if size == 0: return b''
        if this._position + size > this.length(): raise RuntimeError('end of buffer')
        
        data = this._buffer[this._position:this._position + size]
        this._position += size
        
        return bytes(data)
        
    def getBuffer(this):
        assert not this._closed, 'can\'t get buffer with a closed stream'
        return bytes(this._buffer)
        
    def seek(this, offset:int, whence = 0):
        assert not this._closed, 'can\'t seek with a closed stream'
        if   whence == 0:
            this._position  = offset
        elif whence == 1:
            this._position += offset
        elif whence == 2:
            this._position  = this.length() + offset
        this._position = min(this._position, this.length())
        
    def flush(this):
        this._flushed = True
        
    def close(this):
        this.flush()
        this._closed  = True
# end BaksysMemoryStream

class BaksysFileStream:
    def __init__(this, file):
        this._file = file
        
    def __del__(this):
        this.close()
        
    def position(this):
        return this._file.tell()
        
    def length(this):
        origin = this._file.tell()
        this._file.seek(0, 2)
        length = this._file.tell()
        this._file.seek(origin, 0)
        return length
        
    def write(this, buffer:bytes):
        this._file.write(buffer)
        
    def read(this, size:int):
        assert size >= 0, 'negative size'
        if this.position() + size > this.length(): raise RuntimeError('end of buffer')
        if size == 0: return b''
        return this._file.read(size)
        
    def seek(this, offset, whence = 0):
        this._file.seek(offset, whence)
        
    def flush(this):
        this._file.flush()
        
    def close(this):
        this._file.close()
# end BaksysFileStream
        
class BaksysBinaryReader:
    def __init__(this, base):
        this.base = base
        
    def avaiable(this):
        return this.length() - this.position()
        
    def length(this):
        return this.base.length()
        
    def position(this):
        return this.base.position()
        
    def seek(this, offset, whence = 0):
        this.base.seek(offset, whence)
          
    def readBuffer(this, length):
        return this.base.read(length)
        
    def readSByte(this):
        return int.from_bytes(this.readBuffer(1), byteorder='little', signed=True)
        
    def readByte(this):
        return int.from_bytes(this.readBuffer(1), byteorder='little', signed=False)
        
    def readShort(this):
        return int.from_bytes(this.readBuffer(2), byteorder='little', signed=True)
        
    def readInt(this):
        return int.from_bytes(this.readBuffer(4), byteorder='little', signed=True)
        
    def readLong(this):
        return int.from_bytes(this.readBuffer(8), byteorder='little', signed=True)
        
    def readUShort(this):
        return int.from_bytes(this.readBuffer(2), byteorder='little', signed=False)
        
    def readUInt(this):
        return int.from_bytes(this.readBuffer(4), byteorder='little', signed=False)
        
    def readULong(this):
        return int.from_bytes(this.readBuffer(8), byteorder='little', signed=False)
        
    def readFloat(this):
        return struct.unpack('<f', this.readBuffer(4))[0]
        
    def readDouble(this):
        return struct.unpack('<d', this.readBuffer(8))[0]
        
    def readString(this, cp='UTF-8'):
        length = this.readEncodingInt();
        return this.readBuffer(length).decode(cp) if length > 0 else ''
        
    def readEncodingInt(this):
        val = this.readByte();
        ret = val & 0x7F;
        i   = 1
        
        while (val & 0x80) > 0:
            val = this.readByte();
            ret = ret | ((val & 0x7F) << 7*i)
            i += 1
        
        return ret
        
    def flush(this):
        this.base.flush()
        
    def close(this):
        this.base.close()
# end BaksysBinaryReader

class BaksysBinaryWriter:
    def __init__(this, base):
        this.base = base
        
    def length(this):
        return this.base.length()
        
    def position(this):
        return this.base.position()
        
    def seek(this, offset:int, whence = 0):
        this.base.seek(offset, whence)
      
    def writeBuffer(this, buffer):
        this.base.write(buffer)
        
    def writeSByte(this, value:int):
        assert value>=-128 and value<=127, 'out of range'
        
        buf = value.to_bytes(1, byteorder='little', signed=True)
        this.writeBuffer(buf)
        
    def writeByte(this, value:int):
        assert value>=0 and value<=255, 'out of range'
        
        buf = value.to_bytes(1, byteorder='little', signed=False)
        this.writeBuffer(buf)
        
    def writeShort(this, value:int):
        assert value>=-32768 and value<=32767, 'out of range'
        
        buf = value.to_bytes(2, byteorder='little', signed=True)
        this.writeBuffer(buf)
        
    def writeInt(this, value:int):
        assert value>=-2147483648 and value<=2147483647, 'out of range'
        
        buf = value.to_bytes(4, byteorder='little', signed=True)
        this.writeBuffer(buf)
        
    def writeLong(this, value:int):
        assert value>=-0x8000000000000000 and value<=0x7FFFFFFFFFFFFFFF, 'out of range'
        
        buf = value.to_bytes(8, byteorder='little', signed=True)
        this.writeBuffer(buf)
        
    def writeUShort(this, value:int):
        assert value>=0 and value<=65535, 'out of range'
        
        buf = value.to_bytes(2, byteorder='little', signed=False)
        this.writeBuffer(buf)
        
    def writeUInt(this, value:int):
        assert value>=0 and value<=4294967295, 'out of range'
        
        buf = value.to_bytes(4, byteorder='little', signed=False)
        this.writeBuffer(buf)
        
    def writeULong(this, value:int):
        assert value>=0 and value<=0xFFFFFFFFFFFFFFFF, 'out of range'
        
        buf = value.to_bytes(8, byteorder='little', signed=False)
        this.writeBuffer(buf)
        
    def writeFloat(this, value:float):
        buf = struct.pack('<f', value)
        this.writeBuffer(buf)
        
    def writeDouble(this, value:float):
        buf = struct.pack('<d', value)
        this.writeBuffer(buf)
        
    def writeString(this, value:str, cp='UTF-8'):
        buffer = value.encode(cp)
        count  = len(buffer)
        this.writeEncodingInt(count);
        if count > 0:
            this.writeBuffer(buffer)
        
    def writeEncodingInt(this, value:int):
        buf = [value & 0x7F]
        val = value;
        
        while (val & 0x80) > 0:
            val = val >> 7;
            buf.append(value & 0x7F)
            
        this.writeBuffer(bytes(buf))
        
    def flush(this):
        this.base.flush()
        
    def close(this):
        this.base.close()
# end BaksysBinaryWriter
