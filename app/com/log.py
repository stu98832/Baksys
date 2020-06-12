import os
import logging
import traceback

class BaksysLogger:
    def __init__(this, path):
        this.logPath = path
        dirname = os.path.dirname(this.logPath)
        if not os.path.exists(dirname): 
            os.makedirs(dirname)
            
        this.logFormat  = '%(asctime)s [%(name)s] %(levelname)-7s : %(message)s'
        this.dateFormat = '%y/%m/%d %H:%M:%S'
        
        this.format = logging.Formatter(this.logFormat, datefmt=this.dateFormat)
        
        error_log = logging.FileHandler(this.logPath)
        error_log.setLevel(logging.ERROR)
        error_log.setFormatter(this.format)
        
        this.logger = logging.getLogger('baksys')
        this.logger.setLevel(logging.DEBUG)
        this.logger.addHandler(error_log)
        
    def error(this, message, error = None):
        if error:
            ename = error.__class__.__name__ 
            trace = traceback.format_exc()
            this.logger.error('%s. reason : [%s] %s \n%s' % (message, ename, error, trace))
        else:
            this.logger.error('%s.' % (message))
