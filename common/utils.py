import os
import sys
import time
import traceback


def log_info(_msg):
    print('INFO: {}'.format(_msg))
    sys.stdout.flush()


def log_error(_err):
    print('ERROR: {}'.format(str(_err)))
    traceback.print_exc()
    sys.stderr.flush()


def check_rsp_code(_rsp):
    if _rsp.status_code == 200:
        return _rsp.text
    else:
        raise Exception(str(_rsp))

def redis_ready(redis):
    try:
        rs = redis.ping()
        log_info('REDIS READY !!!! ')
        log_info(rs)
        return True
    except Exception as e:
        s = 'REDIS NOT READY  %s   ' % (str(e))
        log_error(s)
        return False

import threading
def setInterval(func, sec):
    def inner():
        while function.isAlive():
            func()
            time.sleep(sec)
    function = type("setInterval", (), {}) # not really a function I guess
    function.isAlive = lambda: function.vars["isAlive"]
    function.vars = {"isAlive": True}
    function.cancel = lambda: function.vars.update({"isAlive": False})
    thread = threading.Timer(sec, inner)
    thread.setDaemon(True)
    thread.start()
    return function

class ServiceUrls():
    def __init__(self):
        self.INVENTORY_URL = os.environ['INVENTORY_SERVICE_SERVICE_HOST'] + ':' + os.environ['INVENTORY_SERVICE_SERVICE_PORT']
        self.CUSTOMER_URL = os.environ['CUSTOMER_SERVICE_SERVICE_HOST'] + ':' + os.environ['CUSTOMER_SERVICE_SERVICE_PORT']
        self.BILLING_URL = os.environ['BILLING_SERVICE_SERVICE_HOST'] + ':' + os.environ['BILLING_SERVICE_SERVICE_PORT']
        self.ORDER_URL = os.environ['ORDER_SERVICE_SERVICE_HOST'] + ':' + os.environ['ORDER_SERVICE_SERVICE_PORT']
        self.PRODUCT_URL = os.environ['PRODUCT_SERVICE_SERVICE_HOST'] + ':' + os.environ['PRODUCT_SERVICE_SERVICE_PORT']
        self.urls = [self.INVENTORY_URL,self.CUSTOMER_URL,self.BILLING_URL,self.ORDER_URL,self.PRODUCT_URL]

