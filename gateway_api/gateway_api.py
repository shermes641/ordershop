import json

import requests
from flask import request, abort
from flask import Flask

from common.utils import check_rsp_code, redis_ready, log_info, ServiceUrls, setInterval
from lib.event_store import EventStore

app = Flask(__name__)
store = EventStore()

restart = False
redis_cnt = 0
restart_cnt = 5

def ready():
    return redis_cnt > 2 * restart_cnt

def proxy_command_request(_base_url):
    """
    Helper function to proxy POST, PUT and DELETE requests to the according service.

    :param _base_url: The URL of the service.
    """

    # handle POST
    if request.method == 'POST':

        try:
            values = json.loads(request.data)
        except Exception:
            raise ValueError("cannot parse json body {}".format(request.data))

        rsp = requests.post(_base_url.format(request.full_path), json=values)
        return check_rsp_code(rsp)

    # handle PUT
    if request.method == 'PUT':

        try:
            values = json.loads(request.data)
        except Exception:
            raise ValueError("cannot parse json body {}".format(request.data))

        rsp = requests.put(_base_url.format(request.full_path), json=values)
        return check_rsp_code(rsp)

    # handle DELETE
    if request.method == 'DELETE':
        rsp = requests.delete(_base_url.format(request.full_path))
        return check_rsp_code(rsp)


@app.route('/billings', methods=['GET'])
@app.route('/billing/<billing_id>', methods=['GET'])
@app.route('/health', methods=['GET'])
@app.route('/restart', methods=['GET'])
def billing_query(billing_id=None):
    result = None
    global restart
    if 'health' in request.path:
        if restart:
            abort(500)
        else:
            return json.dumps(True)
    elif not ready():
        abort(503)
    elif 'restart' in request.path:
        restart = True
        return json.dumps(True)
    elif billing_id:
        result = store.find_one('billing', billing_id)
    else:
        result = store.find_all('billing')
    return json.dumps(result)


# noinspection PyUnusedLocal
@app.route('/billing', methods=['POST'])
@app.route('/billings', methods=['POST'])
@app.route('/billing/<billing_id>', methods=['PUT'])
@app.route('/billing/<billing_id>', methods=['DELETE'])
def billing_command(billing_id=None):
    if not ready():
        abort(503)
    else:
        return proxy_command_request('http://billing-service:5000{}')


@app.route('/customers', methods=['GET'])
@app.route('/customer/<customer_id>', methods=['GET'])
def customer_query(customer_id=None):
    result = None
    if not ready():
        abort(503)
    elif customer_id:
        result = store.find_one('customer', customer_id)
    else:
        result = store.find_all('customer')
    return json.dumps(result)


# noinspection PyUnusedLocal
@app.route('/customer', methods=['POST'])
@app.route('/customers', methods=['POST'])
@app.route('/customer/<customer_id>', methods=['PUT'])
@app.route('/customer/<customer_id>', methods=['DELETE'])
def customer_command(customer_id=None):
    if not ready():
        abort(503)
    else:
        return proxy_command_request('http://customer-service:5000{}')


@app.route('/products', methods=['GET'])
@app.route('/product/<product_id>', methods=['GET'])
def product_query(product_id=None):
    result = None
    if not ready():
        abort(503)
    elif product_id:
        result = store.find_one('product', product_id)
    else:
        result = store.find_all('product')
    return json.dumps(result)


# noinspection PyUnusedLocal
@app.route('/product', methods=['POST'])
@app.route('/products', methods=['POST'])
@app.route('/product/<product_id>', methods=['PUT'])
@app.route('/product/<product_id>', methods=['DELETE'])
def product_command(product_id=None):
    if not ready():
        abort(503)
    else:
        return proxy_command_request('http://product-service:5000{}')


@app.route('/inventory', methods=['GET'])
@app.route('/inventory/<inventory_id>', methods=['GET'])
def inventory_query(inventory_id=None):
    result = None
    if not ready():
        abort(503)
    elif inventory_id:
        result = store.find_one('inventory', inventory_id)
    else:
        result = store.find_all('inventory')
    return json.dumps(result)


# noinspection PyUnusedLocal
@app.route('/inventory', methods=['POST'])
@app.route('/inventory/<inventory_id>', methods=['PUT'])
@app.route('/inventory/<inventory_id>', methods=['DELETE'])
def inventory_command(inventory_id=None):
    result = None
    if not ready():
        abort(503)
    else:
        return proxy_command_request('http://inventory-service:5000{}')


@app.route('/orders', methods=['GET'])
@app.route('/order/<order_id>', methods=['GET'])
@app.route('/orders/unbilled', methods=['GET'])
def order_query(order_id=None):
    result = None
    if not ready():
        abort(503)
    # handle additional query 'unbilled orders'
    elif request.path.endswith('/orders/unbilled'):
        rsp = requests.get('http://order-service:5000/orders/unbilled')
        check_rsp_code(rsp)
        return rsp.text
    elif order_id:
        result = store.find_one('order', order_id)
    else:
        result = store.find_all('order')
    return json.dumps(result)


# noinspection PyUnusedLocal
@app.route('/order', methods=['POST'])
@app.route('/orders', methods=['POST'])
@app.route('/order/<order_id>', methods=['PUT'])
@app.route('/order/<order_id>', methods=['DELETE'])
def order_command(order_id=None):
    if not ready():
        abort(503)
    else:
        return proxy_command_request('http://order-service:5000{}')


@app.route('/report', methods=['GET'])
def report():
    result = None
    if not ready():
        abort(503)
    else:
        result = {
            "products": store.find_all('product'),
            "inventory": store.find_all('inventory'),
            "customers": store.find_all('customer'),
            "orders": store.find_all('order'),
            "billings": store.find_all('billing')
        }

        return json.dumps(result)


def redis_chk(redis):
    global store, redis_cnt
    redis_down = not redis_ready(redis)
    log_info('redis_chk %s  down ? %s' % (redis_cnt, redis_down))
    if redis_down:
        redis_cnt = 0
    else:
        redis_cnt += 1
    if redis_cnt == restart_cnt:
        service_urls = ServiceUrls()
        log_info(service_urls.urls)
        for u in service_urls.urls:
            url = 'http://' + u + '/restart'
            r = requests.get(url=url)
            log_info(url)
            log_info(r.status_code)

    """
    if redis_cnt < 3 and redis_down:
        log_info('!!!!!!!!!!!!!!!!!!!!!!!!!!! PUBLISH REDIS RESTART !!!!!!!!!!!!!!!!!')
        store.publish('redis', 'restart')
    """


setInterval(lambda: redis_chk(store.redis), 2)
