import socket
import time
import threading
from baksys.io import *

class BaksysClientSocket:
    CHUNK_SIZE = 4096

    def __init__(this, socket = None, address=('0.0.0.0', 0)):
        this._socket      = socket
        this._address     = address
        this._connecting  = False if not socket else True
        this._thread      = None
        this.onReceive    = lambda c,p: None
        this.onDisconnect = lambda c: None
            
    def address(this):
        return this._address
    
    def isConnecting(this):
        return this._connecting
        
    def close(this):
        if this._connecting:
            this.disconnect()
    
    def connect(this, ip, port):
        if this._connecting:
            raise RuntimeError('connection established')
        
        this._socket  = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        this._address = (ip, port)
        this._socket.connect(this._address)
        this._socket.setblocking(False)
        this._connecting = True
            
    def disconnect(this):
        if not this._connecting or not this._socket:
            raise RuntimeError('no connection')
            
        this._connecting = False
        if this._thread and not threading.current_thread():
            this._thread.join()
        
    def send(this, data):
        if not this._connecting or not this._socket:
            raise RuntimeError('no connection')
            
        packet = []
        packetSize = len(data)
        packet.extend(packetSize.to_bytes(4, byteorder='little', signed = True))
        packet.extend(data)
        sendedSize = 0
        
        while sendedSize < len(packet):
            try:
                partOfPacket = packet[sendedSize:]
                sendedSize += this._socket.send(bytes(partOfPacket))
            except BlockingIOError:
                continue
        
    def startReceive(this):
        if not this._connecting or not this._socket:
            raise RuntimeError('no connection')
            
        this._thread = threading.Thread(target = this._recive, daemon=True)
        this._thread.start()
        
    def _recive(this):
        try:
            rawData = []
            while this._connecting:
                time.sleep(0.1)
                try:
                    data = this._socket.recv(BaksysClientSocket.CHUNK_SIZE)
                    if not data: break
                    rawData.extend(data)
                    while True:
                        if len(rawData) < 4: break
                        packetSize = int.from_bytes(bytes(rawData[:4]), byteorder='little', signed = False)
                        if len(rawData) < (packetSize+4): break
                        ms = BaksysMemoryStream(rawData[4:4+packetSize])
                        br = BaksysBinaryReader(ms)
                        rawData = rawData[4+packetSize:]
                        this.onReceive(this, br)
                except BlockingIOError:
                    continue
                except ConnectionResetError:
                    break
        finally:    
            this.onDisconnect(this)
            this._socket.close()
            this._connecting = False
    # end _recive
# end BaksysClientSocket

class BaksysServerSocket:
    def __init__(this):
        this._socket    = None
        this._listening = False
        this._address   = ('0.0.0.0', 0)
        this._thread    = None
        this.onAccept   = lambda s,c: None
        this.onClose    = lambda s: None
            
    def address(this):
        return this._address
        
    def close(this):
        if this._listening:
            this.shutdown()
     
    def start(this, ip, port, backlog=10):
        if this._listening:
            raise RuntimeError('server is listening')
           
        this._socket  = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        this._address = (ip, port)
        this._socket.bind(this._address)
        this._socket.listen(backlog)
        this._socket.setblocking(False)
        this._listening = True
        
    def isListening(this):
        return this._listening
        
    def startAccept(this):
        if not this._listening or not this._socket:
            raise RuntimeError('server is not listening')
            
        this._thread = threading.Thread(target = this._accept, daemon=True)
        this._thread.start()
        
    def shutdown(this):
        if not this._listening or not this._socket:
            raise RuntimeError('server is not listening')
            
        this._listening = False
        if this._thread and not threading.current_thread():
            this._thread.join()
        
    def _accept(this):
        try:
            while this._listening:
                time.sleep(0.1)
                try:
                    sock, addr = this._socket.accept()
                    client = BaksysClientSocket(sock, addr)
                    this.onAccept(this, client)
                except BlockingIOError:
                    continue
        finally:    
            this.onClose(this)
            this._socket.close()
            this._listening = False
# end BaksysServerSocket
        