import os
import baksys.config as config

BAKSYS_HOME      = os.path.expanduser('~/.baksys')
BAKSYS_REMOTE    = os.path.join(BAKSYS_HOME, 'remote')
BAKSYS_LOGS      = os.path.join(BAKSYS_HOME, 'logs')
BAKSYS_ERROR_LOG = os.path.join(BAKSYS_LOGS, 'server.error.log')
BAKSYS_CONFIG    = os.path.join(BAKSYS_HOME, 'server.json')
BAKSYS_PORT      = 20003

config.set('backup_path', BAKSYS_REMOTE)
config.set('logs_path'  , BAKSYS_ERROR_LOG)

if os.path.exists(BAKSYS_CONFIG): 
    config.load(BAKSYS_CONFIG)