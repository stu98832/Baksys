import os
import json
from   app.com.log import *

BAKSYS_HOME      = os.path.expanduser('~/.baksys')
BAKSYS_TEMPDIR   = os.path.join(BAKSYS_HOME, 'temp')
BAKSYS_BACKUP    = os.path.join(BAKSYS_HOME, 'backup')
BAKSYS_LOGS      = os.path.join(BAKSYS_HOME, 'logs')
BAKSYS_ERROR_LOG = os.path.join(BAKSYS_LOGS, 'client.error.log')
BAKSYS_CONFIG    = os.path.join(BAKSYS_HOME, 'client.json')
BAKSYS_PORT      = 20003

config = { }
if not config:
    config['backup_path'] = BAKSYS_BACKUP
    if os.path.exists(BAKSYS_CONFIG): 
        with open(BAKSYS_CONFIG, 'r') as file:
            config = json.load(file)
            
logger = BaksysLogger(BAKSYS_ERROR_LOG)

def saveConfig():
    with open(BAKSYS_CONFIG, 'w') as file:
        json.dump(config, file)
_initialize = False