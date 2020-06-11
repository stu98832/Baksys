import os
import json

_attr = { }

def clear():
    global _attr
    _attr = { }
    
def load(filename):
    global _attr
    full_path = os.path.abspath(os.path.expanduser(filename))
    
    if not os.path.exists(full_path):
        raise FileNotFoundError('can\'t load configure file from \'%s\'' % full_path)
    
    with open(full_path, 'r') as conf:
        _attr.update(json.load(conf))

def save(filename):
    full_path = os.path.abspath(os.path.expanduser(filename))
    dir_path  = os.path.dirname(filename)
    
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    
    with open(full_path, 'w') as conf:
        json.dump(_attr, conf)
    
def get(name):
    return _attr[name]

def set(name, value):
    global _attr
    _attr[name] = value