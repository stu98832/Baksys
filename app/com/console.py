import os
def progressBar(message, percent):
    barlen   = os.get_terminal_size().columns-len(message)-3
    status   = '\r%%s[%%-%ds]' % (barlen)
    bar      = '='*(int((barlen-1)*percent))+'>'
    print(status % (message, bar), end='')

def askYesNo(message):
    while True:
        resp = input('%s (Y/N) ' % (message))
        
        if 'Y' == resp or 'y' == resp:
            return True
        elif 'N' == resp or 'n' == resp:
            return False
        else:
            print('must be \'Y\' or \'N\'')