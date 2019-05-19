import json
import logging
from datetime import timedelta

import requests
from flask import Flask
from flask import request, abort
from timeloop import Timeloop

from common.service_base import ServiceBase
from common.utils import check_rsp_code, log_info, ChkClass, PREFIX, ServiceUrls, log_error, services_chk
from lib.event_store import EventStore


class GatewayService(ServiceBase):
    def __init__(self):
        self.chk_class = ChkClass('gateway')
        self.store = EventStore(self.chk_class.name)
        self.init_store(self.chk_class, self.store)

    def stores_ready(self, keys=None, ret_val=1, msg='?????????????'):
        try:
            x = "','" + PREFIX
            y = "gs.chk_class.res = self.store.redis.exists('" + PREFIX + x.join(keys) + "')"
            exec(y)
            log_info('$$$ %s' % gs.chk_class.res)
            if int(gs.chk_class.res) != ret_val:
                exec(y)
                log_info('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ %s' % gs.chk_class.res)
            return int(gs.chk_class.res) == ret_val
        except Exception as e:
            s = '!!!!!!!!!!!!!!!!!!!!!!! redis_ready REDIS NOT READY  %s   %s' % (str(e), msg)
            log_error(s)
            return False

    def proxy_command_request(self, _base_url):
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


gs = GatewayService()

tl = Timeloop()


@tl.job(interval=timedelta(seconds=3))
def rc():
    gs.redis_chk(gs.chk_class, gs.store)


@tl.job(interval=timedelta(seconds=5))
def rc1():
    gs.chk_class.service = ServiceUrls()
    res = gs.stores_ready(gs.chk_class.service.names, len(gs.chk_class.service.names), 't1 rc1')
    ret = ''  # None
    # noinspection PyPep8
    if res == False:
        ret = 'Store Error rc1'
    services_chk(gs.chk_class, ret)


tl.start()

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(gs.chk_class.service.LOGLEVEL)


@app.route('/billings', methods=['GET'])
@app.route('/billing/<billing_id>', methods=['GET'])
@app.route('/health', methods=['GET'])
@app.route('/ready', methods=['GET'])
@app.route('/restart', methods=['GET'])
def billing_query(billing_id=None):
    """
    Route billing requests
    :param billing_id: Get a particular bill
    :return:
    """
    result = None
    if 'health' in request.path:
        if gs.chk_class.restart:
            abort(500)
        else:
            gs.store.redis.psetex(PREFIX + gs.chk_class.name, 7000, PREFIX + gs.chk_class.name)
            return json.dumps(True)
    elif 'ready' in request.path:
        if gs.chk_redis_store_bad(gs.chk_class, gs.store):
            abort(503)
        else:
            return json.dumps(True)
    elif gs.chk_class.not_ready:
        abort(503)
    elif 'restart' in request.path:
        gs.chk_class.restart = True
        return json.dumps(True)
    elif billing_id:
        result = gs.store.find_one('billing', billing_id)
    else:
        result = gs.store.find_all('billing')
    return json.dumps(result)


# noinspection PyUnusedLocal
@app.route('/billing', methods=['POST'])
@app.route('/billings', methods=['POST'])
@app.route('/billing/<billing_id>', methods=['PUT'])
@app.route('/billing/<billing_id>', methods=['DELETE'])
def billing_command(billing_id=None):
    if gs.chk_class.not_ready:
        abort(503)
    else:
        return gs.proxy_command_request('http://billing-service:5000{}')


@app.route('/customers', methods=['GET'])
@app.route('/customer/<customer_id>', methods=['GET'])
def customer_query(customer_id=None):
    result = None
    if gs.chk_class.not_ready:
        abort(503)
    elif customer_id:
        result = gs.store.find_one('customer', customer_id)
    else:
        result = gs.store.find_all('customer')
    return json.dumps(result)


# noinspection PyUnusedLocal
@app.route('/customer', methods=['POST'])
@app.route('/customers', methods=['POST'])
@app.route('/customer/<customer_id>', methods=['PUT'])
@app.route('/customer/<customer_id>', methods=['DELETE'])
def customer_command(customer_id=None):
    if gs.chk_class.not_ready:
        abort(503)
    else:
        return gs.proxy_command_request('http://customer-service:5000{}')


@app.route('/products', methods=['GET'])
@app.route('/product/<product_id>', methods=['GET'])
def product_query(product_id=None):
    result = None
    if gs.chk_class.not_ready:
        abort(503)
    elif product_id:
        result = gs.store.find_one('product', product_id)
    else:
        result = gs.store.find_all('product')
    return json.dumps(result)


# noinspection PyUnusedLocal
@app.route('/product', methods=['POST'])
@app.route('/products', methods=['POST'])
@app.route('/product/<product_id>', methods=['PUT'])
@app.route('/product/<product_id>', methods=['DELETE'])
def product_command(product_id=None):
    if gs.chk_class.not_ready:
        abort(503)
    else:
        return gs.proxy_command_request('http://product-service:5000{}')


@app.route('/inventory', methods=['GET'])
@app.route('/inventory/<inventory_id>', methods=['GET'])
def inventory_query(inventory_id=None):
    result = None
    if gs.chk_class.not_ready:
        abort(503)
    elif inventory_id:
        result = gs.store.find_one('inventory', inventory_id)
    else:
        result = gs.store.find_all('inventory')
    return json.dumps(result)


# noinspection PyUnusedLocal
@app.route('/inventory', methods=['POST'])
@app.route('/inventory/<inventory_id>', methods=['PUT'])
@app.route('/inventory/<inventory_id>', methods=['DELETE'])
def inventory_command(inventory_id=None):
    result = None
    if gs.chk_class.not_ready:
        abort(503)
    else:
        return gs.proxy_command_request('http://inventory-service:5000{}')


@app.route('/orders', methods=['GET'])
@app.route('/order/<order_id>', methods=['GET'])
@app.route('/orders/unbilled', methods=['GET'])
def order_query(order_id=None):
    result = None
    if gs.chk_class.not_ready:
        abort(503)
    # handle additional query 'unbilled orders'
    elif request.path.endswith('/orders/unbilled'):
        rsp = requests.get('http://order-service:5000/orders/unbilled')
        check_rsp_code(rsp)
        return rsp.text
    elif order_id:
        result = gs.store.find_one('order', order_id)
    else:
        result = gs.store.find_all('order')
    return json.dumps(result)


# noinspection PyUnusedLocal
@app.route('/order', methods=['POST'])
@app.route('/orders', methods=['POST'])
@app.route('/order/<order_id>', methods=['PUT'])
@app.route('/order/<order_id>', methods=['DELETE'])
def order_command(order_id=None):
    if gs.chk_class.not_ready:
        abort(503)
    else:
        return gs.proxy_command_request('http://order-service:5000{}')


@app.route('/report', methods=['GET'])
def report():
    if gs.chk_class.not_ready:
        abort(503)
    else:
        result = {
            "products": gs.store.find_all('product'),
            "inventory": gs.store.find_all('inventory'),
            "customers": gs.store.find_all('customer'),
            "orders": gs.store.find_all('order'),
            "billings": gs.store.find_all('billing')
        }

        return json.dumps(result)


gs.chk_class.not_ready = False
gs.chk_class.max_not_ready_cnt = 11
