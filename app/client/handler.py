import os
import shutil
from   baksys.event       import *
from   app.client.setting import *
import app.com.packet        as packet
import app.com.packet.backup

def handleBackup(remoteBackup, message):
    subtype = message.readByte()
    if subtype == packet.backup.REQUEST_TYPE_LIST:
        count = message.readEncodingInt()
        backupList = []
        for i in range(count):
            path    = message.readString()
            orgpath = message.readString()
            size    = message.readLong()
            crc     = message.readUInt()
            backupList.append({                         \
                'name'        : os.path.basename(path), \
                'path'        : path,                   \
                'origin_path' : orgpath,                \
                'size'        : size,                   \
                'crc'         : crc,                    \
            })
        remoteBackup.setResponse(backupList)
    # end REQUEST_TYPE_LIST
    elif subtype == packet.backup.REQUEST_TYPE_UPDATE_LIST:
        count = message.readEncodingInt()
        updateList = []
        for i in range(count):
            updateList.append(message.readString())
        remoteBackup.setResponse(updateList)
    # end REQUEST_TYPE_UPDATE_LIST
# end handleBackup

def handleUpload(remoteBackup, message):
    subtype = message.readByte()
    if   subtype == packet.backup.UPLOAD_DOWNLOAD_START:
        pass
    # end UPLOAD_DOWNLOAD_START
    elif subtype == packet.backup.UPLOAD_DOWNLOAD_BREAK:
        remoteBackup.uploadInterrupt()
        remoteBackup.lastOperationError = 'operation has been interrupted by remote server'
        remoteBackup.setResponse(False)
    # end UPLOAD_DOWNLOAD_BREAK
    

def handleDownload(remoteBackup, message):
    subtype = message.readByte()
    
    if   subtype == packet.backup.UPLOAD_DOWNLOAD_START:
        remoteBackup.downloadFile['total_size'] = message.readLong()
        if not os.path.exists(BAKSYS_TEMPDIR):
            os.makedirs(BAKSYS_TEMPDIR)
        remoteBackup.downloadFile['file'] = open(remoteBackup.downloadFile['temp'], 'wb')
        remoteBackup.setResponse(True)
    # end UPLOAD_DOWNLOAD_START
    elif subtype == packet.backup.UPLOAD_DOWNLOAD_BREAK:
        remoteBackup.lastOperationError = 'operation has been interrupted by remote server'
        remoteBackup.setResponse(False)
    # end UPLOAD_DOWNLOAD_BREAK
    elif subtype == packet.backup.UPLOAD_DOWNLOAD_CONTINUE:
        try:
            if not remoteBackup.downloadFile:
                remoteBackup.downloadInterrupt()
                return
            offset = message.readLong()
            size   = message.readLong()
            data   = message.readBuffer(size)
            remoteBackup.downloadFile['offset'] = offset
            remoteBackup.downloadFile['size']  += size
            remoteBackup.downloadFile['file'].seek(offset, 0)
            remoteBackup.downloadFile['file'].write(data)
            
            # event invoke
            args = BaksysEventArgs()
            args.progress = remoteBackup.downloadFile['size'] / remoteBackup.downloadFile['total_size']
            remoteBackup.onDownloadProcess.invoke(args)
        except Exception as e:
            remoteBackup.downloadInterrupt()
            remoteBackup.lastOperationError = str(e)
            remoteBackup.setResponse(False)
    # end UPLOAD_DOWNLOAD_CONTINUE
    elif subtype == packet.backup.UPLOAD_DOWNLOAD_FINISH:
        if not remoteBackup.downloadFile:
            remoteBackup.downloadInterrupt()
            return
        remoteBackup.downloadFile['file'].close()
        if os.path.exists(remoteBackup.downloadFile['path']):
            os.remove(remoteBackup.downloadFile['path'])
        shutil.move(remoteBackup.downloadFile['temp'], remoteBackup.downloadFile['path'])
        remoteBackup.downloadFile = { }
        remoteBackup.setResponse(True)
    # end UPLOAD_DOWNLOAD_FINISH
# end handleDownload