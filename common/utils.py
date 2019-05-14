import sys
import traceback
import redis

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
        log_info('REDIS READY')
        log_info(rs)
        return True
    except Exception as e:
        s = 'REDIS NOT READY %s', str(e)
        log_error(s)
        return False
