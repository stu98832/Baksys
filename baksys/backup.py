import os
import zlib
from binascii     import crc32
from baksys.io    import *
from baksys.utils import *
from baksys.event import *

# enum BaksysItemType
class BaksysItemType:
    Null      = 0
    File      = 1
    Directory = 2
    
# abstract class BaksysItem
class BaksysItem:
    def __init__(this, sName, nType):
        this.pkgFile = None
        this.sName   = sName
        this.nType   = nType
        this.nSize   = 0
        
    def read(this, reader):
        this.nSize  = reader.readLong()
        
    def write(this, writer):
        writer.writeByte(this.nType)
        writer.writeString(this.sName)
        this._sizeOffset = writer.position()
        writer.writeLong(0)
        
    def writeSize(this, writer, size = None):
        oldOffset  = writer.position()
        this.nSize = size if size != None else (oldOffset - (this._sizeOffset + 8))
        writer.seek(this._sizeOffset, 0)
        writer.writeLong(this.nSize)
        writer.seek(oldOffset, 0)
# end BaksysItem

# class BaksysFile : BaksysItem
class BaksysFile(BaksysItem):
    CHUNK_SIZE = 4096

    def __init__(this, name, source = None):
        BaksysItem.__init__(this, name, BaksysItemType.File)
        this.sSource = source
        this.nOffset = 0
        this.pReader = None
        
    def check(this):
        if this.pReader == None:
            return False
            
        this.pReader.seek(this.nOffset, 0)
        crc        = 0
        avaiable   = this.nSize
        zlibstream = zlib.decompressobj()
        while avaiable > 0:
            size = min(BaksysFile.CHUNK_SIZE, avaiable)
            compressed = this.pReader.readBuffer(size)
            data       = zlibstream.decompress(compressed)
            crc        = crc32(data, crc) & 0xFFFFFFFF
            avaiable -= size
        return this.nCRC == crc
        
    def extract(this, path, **option):
        if this.pReader == None:
            return
           
        fullPath = os.path.join(path, this.sName)
        override = BaksysUtils.loadOption(option, 'override', False)
        
        if os.path.exists(fullPath) and not override:
            raise FileExistsError('[FileExtract] file has existed at directory \'%s\'' % (path))
             
        if not os.path.exists(path):
            os.makedirs(path)
            
        this.pReader.seek(this.nOffset, 0)
        with open(fullPath, 'wb') as file:
            avaiable   = this.nSize
            zlibstream = zlib.decompressobj()
            while avaiable > 0:
                size = min(BaksysFile.CHUNK_SIZE, avaiable)
                compressed = this.pReader.readBuffer(size)
                data       = zlibstream.decompress(compressed)
                file.write(data)
                avaiable -= size
            file.write(zlibstream.flush())
    # end extract
       
    def read(this, reader):
        BaksysItem.read(this, reader)
        this.nCRC    = reader.readUInt()
        this.nOffset = reader.position()
        this.pReader = reader
        reader.seek(this.nSize, 1)
        
    def write(this, writer):
        BaksysItem.write(this, writer)
        
        this._crcOffset = writer.position()
        writer.writeUInt(0)
        
        this.nOffset = writer.position()
        if this.sSource != None:
            with open(this.sSource, 'rb') as file:
                reader  = BaksysBinaryReader(BaksysFileStream(file))
                avaiable = reader.length()
                this.nSize = avaiable
                
                # write compressed data and calculate
                dataCrc    = 0
                zlibstream = zlib.compressobj(zlib.Z_DEFAULT_COMPRESSION)
                while avaiable > 0:
                    size       = min(BaksysFile.CHUNK_SIZE, avaiable)
                    data       = reader.readBuffer(size)
                    dataCrc    = crc32(data, dataCrc) & 0xFFFFFFFF
                    compressed = zlibstream.compress(data)
                    writer.writeBuffer(compressed)
                    avaiable -= size
                writer.writeBuffer(zlibstream.flush())
        this.nSize = writer.position()-this.nOffset
        
        this.writeCRC(writer, dataCrc)
        BaksysItem.writeSize(this, writer, this.nSize)
        
        # event
        eArgs = BaksysEventArgs()
        eArgs.item  = this
        eArgs.state = 'finished'
        this.pkg.onProgress.invoke(eArgs)
    # end write
        
    def writeCRC(this, writer, crc):
        oldOffset  = writer.position()
        writer.seek(this._crcOffset, 0)
        writer.writeUInt(crc)
        writer.seek(oldOffset, 0)
# end BaksysFile
            
# class BaksysDirectory : BaksysItem    
class BaksysDirectory(BaksysItem):
    def __init__(this, name):
        BaksysItem.__init__(this, name, BaksysItemType.Directory)
        this.aItems = [] # items in this directory 
    
    def extract(this, path, **option):
        override = BaksysUtils.loadOption(option, 'override', False)
        
        if os.path.exists(path) and not override:
            raise FileExistsError('[DirectoryExtract] can\'t extract file \'%s\' to \'%s\'' % (this.sName, path))
             
        realPath = os.path.join(path, this.sName)
        if not os.path.exists(realPath):
            os.makedirs(realPath)
        
        for item in this.aItems:
            item.extract(realPath, **option)
              
    def read(this, reader):
        BaksysItem.read(this, reader)
        count = reader.readInt()
        this.aItems = []
        
        for i in range(count):
            item = BaksysItemParser.read(this.pakFile, reader)
            item.read(reader)
            this.aItems.append(item)
        
    def write(this, writer):
        BaksysItem.write(this, writer)
        writer.writeInt(len(this.aItems))
        
        totalSize = 0
        for item in this.aItems:
            item.write(writer)
            totalSize += item.nSize
            
        BaksysItem.writeSize(this, writer, totalSize)
        
        # event
        eArgs = BaksysEventArgs()
        eArgs.item  = this
        eArgs.state = 'finished'
        this.pkg.onProgress.invoke(eArgs)
    # end write
# end BaksysDirectory

# BaksysItem Parser
class BaksysItemParser:
    def read(pkg, reader):
        objtype = reader.readByte()
        objname = reader.readString()
        obj     = None
        
        if   objtype == BaksysItemType.File:
            obj = BaksysFile(objname)
        elif objtype == BaksysItemType.Directory:
            obj = BaksysDirectory(objname)
            
        if obj != None:
            obj.pakFile = pkg
            
        return obj
# end BaksysItemParser

# Baksys Backup File
class BaksysBackup:
    # Backup file sign
    SIGN = b'BAK1'

    # initialize an empty Backup File
    # name : name of backup file
    def __init__(this): 
        this.sName      = ''      # name of this backup file
        this.nSize      = 0       # size of backup data
        this.nOffset    = 0       # offset of backup data 
        this.nOption    = 0       # option of backup file for extension
        this.sPath      = 0       # original path
        this.pData      = None    # data of this backup file
        this.pFile      = None
        this.onProgress = BaksysEvent()
        this.onFinished = BaksysEvent()
        
    def __del__(this):
        this.close()
        
    # save backup file to specific path
    def save(this, path, **option):
        dirpath  = os.path.dirname(path)
        override = BaksysUtils.loadOption(option, 'override', False)
        
        if os.path.exists(path):
            print('write', path)
            if not override:
                return FileExistsError('[BackupSave] existing file \'%s\'.' % path)
        
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
                
        with open(path, 'wb+') as file:
            stream = BaksysFileStream(file)
            writer = BaksysBinaryWriter(stream)
            writer.writeBuffer(BaksysBackup.SIGN)
            
            sizeOffset = writer.position()
            writer.writeLong(0)
            crcOffset = writer.position()
            writer.writeUInt(0)
            writer.writeShort(0)
            writer.writeInt(0)
            writer.writeString(this.sPath)
            
            this.nOffset = writer.position()
            this.pData.write(writer)
            this.nSize = writer.position() - this.nOffset
            
            this.nCRC = 0
            reader = BaksysBinaryReader(stream)
            reader.seek(this.nOffset, 0)
            while reader.avaiable():
                this.nCRC = crc32(reader.readBuffer(min(4096, reader.avaiable())), this.nCRC) & 0xFFFFFFFF
            
            writer.seek(sizeOffset, 0)
            writer.writeLong(this.nSize)
            writer.writeUInt(this.nCRC)
            writer.writeShort(this.nOffset)
    # end save
    
    # load backup file from specific path
    def load(this, path):
        this.sName = os.path.basename(path)
        
        if not os.path.exists(path):
            return FileNotFoundError('[BackupLoad] non-existing backup file.')
            
        this.pFile = open(path, 'rb')
        reader = BaksysBinaryReader(BaksysFileStream(this.pFile))
        
        # check file sign
        if reader.readBuffer(4) != BaksysBackup.SIGN:
            raise ValueError('[BackupLoad] not a valid backup file.')
           
        # read header
        this.nSize   = reader.readLong()
        this.nCRC    = reader.readUInt()
        this.nOffset = reader.readShort()
        this.nOption = reader.readInt()
        this.sPath   = reader.readString()
            
        # extra information
        
        # data 
        reader.seek(this.nOffset, 0)
        this.pData = BaksysItemParser.read(this, reader)
        this.pData.read(reader)
    # end load
        
    def close(this):
        if this.pFile:
            this.pFile.close()
            this.pFile = None
# end BaksysBackup
