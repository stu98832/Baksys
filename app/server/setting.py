import os
import json
from   app.com.log import *

BAKSYS_HOME      = os.path.expanduser('~/.baksys')
BAKSYS_REMOTE    = os.path.join(BAKSYS_HOME, 'remote')
BAKSYS_LOGS      = os.path.join(BAKSYS_HOME, 'logs')
BAKSYS_ERROR_LOG = os.path.join(BAKSYS_LOGS, 'server.error.log')
BAKSYS_CONFIG    = os.path.join(BAKSYS_HOME, 'server.json')
BAKSYS_PORT      = 20003

config = { }
if not config:
    config['backup_path'] = BAKSYS_REMOTE
    if os.path.exists(BAKSYS_CONFIG): 
        with open(BAKSYS_CONFIG, 'r') as file:
            config = json.load(file)
        
logger = BaksysLogger(BAKSYS_ERROR_LOG)

def saveConfig():
    with open(BAKSYS_CONFIG, 'w') as file:
        json.dump(config, file, indent=4)