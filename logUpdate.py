import time
import corpDB
import historyDB
from staticClasses import settings

def countdown(t):
    while t:
        mins, secs = divmod(t, 60)
        timeformat = ' Next update in: {:02d}:{:02d}'.format(mins, secs)
        print(timeformat, end='\r')
        time.sleep(1)
        t -= 1
    print('updating...', end = '\r')

while True:
    corpDB.updateAll()
    historyDB.updateAll()
    countdown(900)