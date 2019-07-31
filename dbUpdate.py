#!/usr/bin/env python
import sys
import time
import corpDB
import logging
import historyDB
from Auth import authenticate
from swagger_client.rest import ApiException

#----------------------------------------------------------------------
def countdown(t):
    """display a countdown of the provided input in seconds"""
    while t:
        mins, secs = divmod(t, 60)
        timeformat = ' Next update in: {:02d}:{:02d}'.format(mins, secs)
        print(timeformat, end='\r')
        time.sleep(1)
        t -= 1
    print('updating...', end = '\r')

#----------------------------------------------------------------------
def dbUpdate():
    """update both corp and history db"""

    try:
        corpDB.updateAll()
        historyDB.updateAll()
    except ApiException as AE:
        print("A problem with the API has occurred.")
        return [False, AE]
    except ConnectionError as CE:
        print("No internet connectivity.")
        return [False, CE]
    except Exception:
        raise
    else:
        return [True, '']


if __name__ == "__main__":
    countdownTime = 900
    logging.basicConfig(format = '%(asctime)s: %(message)s',
                    filename='eveHistory.log',
                    level = logging.INFO)

    if sys.argv[1] == 'login':
        authenticate(forceLogin=True)

    while True:
        dbUpdated, reason = dbUpdate()
        if dbUpdated:
            countdownTime = 900
            logging.warn(f"Database updated.")
        elif isinstance(reason, ConnectionError):
            countdownTime = 1800
            logging.warn(f"No network connectivity.")
        elif isinstance(reason, ApiException):
            countdownTime = 1800
            logging.error(f"Api Exception: {reason}")

        countdown(countdownTime)