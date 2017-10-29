import time
from staticClasses import settings
from DB import LogDBUpdate, DBUpdate

def countdown(t):
    while t:
        mins, secs = divmod(t, 60)
        timeformat = ' Next update in: {:02d}:{:02d}'.format(mins, secs)
        print(timeformat, end='\r')
        time.sleep(1)
        t -= 1
    print('updating...', end = '\r')

while True:
    DBUpdate.updateAll()
    LogDBUpdate.updateAllLogs()
    countdown(900)