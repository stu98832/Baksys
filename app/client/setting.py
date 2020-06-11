import os
import baksys.config as config

BAKSYS_HOME      = os.path.expanduser('~/.baksys')
BAKSYS_BACKUP    = os.path.join(BAKSYS_HOME, 'backup')
BAKSYS_LOGS      = os.path.join(BAKSYS_HOME, 'logs')
BAKSYS_ERROR_LOG = os.path.join(BAKSYS_LOGS, 'client.error.log')
BAKSYS_CONFIG    = os.path.join(BAKSYS_HOME, 'client.json')
BAKSYS_PORT      = 20003

# default config
config.set('backup_path', BAKSYS_BACKUP)
config.set('logs_path'  , BAKSYS_ERROR_LOG)

if os.path.exists(BAKSYS_CONFIG): 
    config.load(BAKSYS_CONFIG)