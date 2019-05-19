import os
import sys
import traceback

import requests

MAX_CONNECT_TRIES = 10

PREFIX = 'powerhive_srv_'


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


class ChkClass:
    def __init__(self, name='undefined'):
        self.name = name
        self.restart = False
        self.redis_cnt = 0
        self.redis_down = False
        self.restart_cnt = 5
        self.not_ready = False
        self.not_ready_msg = ''
        self.not_ready_cnt = 0
        self.max_not_ready_cnt = 3
        self.mutex = False
        self.cnt = 0
        self.store_down = False
        self.service = ServiceUrls()
        self.res = None


class ServiceUrls:
    def __init__(self):
        self.INVENTORY_URL = os.environ['INVENTORY_SERVICE_SERVICE_HOST'] + ':' + os.environ['INVENTORY_SERVICE_SERVICE_PORT']
        self.CUSTOMER_URL = os.environ['CUSTOMER_SERVICE_SERVICE_HOST'] + ':' + os.environ['CUSTOMER_SERVICE_SERVICE_PORT']
        self.BILLING_URL = os.environ['BILLING_SERVICE_SERVICE_HOST'] + ':' + os.environ['BILLING_SERVICE_SERVICE_PORT']
        self.ORDER_URL = os.environ['ORDER_SERVICE_SERVICE_HOST'] + ':' + os.environ['ORDER_SERVICE_SERVICE_PORT']
        self.PRODUCT_URL = os.environ['PRODUCT_SERVICE_SERVICE_HOST'] + ':' + os.environ['PRODUCT_SERVICE_SERVICE_PORT']
        self.LOGLEVEL = os.environ['LOGLEVEL']
        if self.LOGLEVEL is None:
            self.LOGLEVEL = 'WARNING'
        self.urls = [self.INVENTORY_URL, self.CUSTOMER_URL, self.BILLING_URL, self.ORDER_URL, self.PRODUCT_URL]
        self.names = ['inventory', 'customer', 'billing', 'order', 'product', 'crm']


def restart_services(_class: ChkClass):
    for u in _class.service.urls:
        try:
            url = 'http://' + u + '/restart'
            r = requests.get(url=url)
            s = 'RESTART %s    %s' % (url, r.status_code)
            log_info(s)
        except Exception as e:
            log_error('restart_services  %s   ERROR: %s' % (url, e))


def redis_ready(redis, keys=None, ret_val=1, msg='?????????????'):
    try:
        j = ',' + PREFIX
        res = redis.exists(PREFIX + j.join(keys))
        return int(res) == ret_val
    except Exception as e:
        s = '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! redis_ready REDIS NOT READY  %s   %s' % (str(e), msg)
        log_error(s)
        return False

def services_ready(_class):
    """
    :return:    True if all services are ready
    """
    ret = None
    if _class.mutex is True:
        return ret
    _class.mutex = True
    try:
        ret = ''
        for u in _class.service.urls:
            url = 'http://' + u + '/ready'

            r = requests.get(url=url)
            s = 'Ready %s    %s' % (url, r.status_code)
            if r.status_code != 200:
                ret = s
                _class.mutex = False
    except Exception as e:
        ret = 'service_ready EXCEPTION: %s ' % str(e)
        log_error(ret)
    finally:
        _class.mutex = False
        return ret

def services_chk(_class: ChkClass, ret=None):
    if ret is None:
        ret = services_ready(_class)
    if ret is not None:
        if ret == '':
            _class.not_ready_cnt = 0
            _class.not_ready = False
        else:
            _class.not_ready_cnt += 1
            if _class.not_ready_cnt > _class.max_not_ready_cnt:
                _class.not_ready = True
        _class.not_ready_msg = ret

    if _class.not_ready_cnt > _class.max_not_ready_cnt:
        log_info('!!!!!!!!!!!!!!!!! RESTARTING SERVICES !!!!!!!!!!!!!!!!!!!!!!!!')
        restart_services(_class)
        _class.not_ready_cnt = 0
        _class.not_ready = ''
