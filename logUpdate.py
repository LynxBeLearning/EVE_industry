import time
import corpDB
import logging
import historyDB
from staticClasses import settings
from swagger_client.rest import ApiException

logging.basicConfig(format = '%(asctime)s: %(message)s',
                    filename='eveHistory.log',
                    level = logging.INFO)

def countdown(t):
    while t:
        mins, secs = divmod(t, 60)
        timeformat = ' Next update in: {:02d}:{:02d}'.format(mins, secs)
        print(timeformat, end='\r')
        time.sleep(1)
        t -= 1
    print('updating...', end = '\r')

while True:
    try:
        corpDB.updateAll()
        historyDB.updateAll()
    except ApiException as AE:
        logging.error(f"Api Exception: {AE}")
        print("A problem with the API has occurred, see log for details.\n\n")
        countdownTime = 1800
    except ConnectionError:
        logging.warn(f"No network connectivity.")
        countdownTime = 1800
    else:
        logging.warn(f"Database updated.")
        countdownTime = 900
    finally:
        countdown(countdownTime)