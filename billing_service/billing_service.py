import json
import time
import uuid
from datetime import timedelta

import requests
from flask import Flask
from flask import request, abort
from timeloop import Timeloop

from common.service_base import ServiceBase
from common.utils import log_error, log_info, ChkClass
from lib.event_store import EventStore


class BillingService(ServiceBase):
    def __init__(self):
        self.chk_class = ChkClass('billing')
        self.store = EventStore(self.chk_class.name)
        self.init_store(self.chk_class, self.store)

    @staticmethod
    def create_billing(_order_id):
        """
        Create a billing entity.

        :param _order_id: The order ID the billing belongs to.
        :return: A dict with the entity properties.
        """
        return {
            'id': str(uuid.uuid4()),
            'order_id': _order_id,
            'done': time.time()
        }

    def order_created(self, item):
        try:
            msg_data = json.loads(item[1][0][1]['entity'])
            customer = self.store.find_one('customer', msg_data['customer_id'])
            products = [self.store.find_one('product', product_id) for product_id in msg_data['product_ids']]
            msg = """Dear {}!
    
    Please transfer € {} with your favourite payment method.
    
    Cheers""".format(customer['name'], sum([int(product['price']) for product in products]))

            requests.post('http://msg-service:5000/email', json={
                "to": customer['email'],
                "msg": msg
            })
        except Exception as e:
            log_error(e)

    def billing_created(self, item):
        try:
            msg_data = json.loads(item[1][0][1]['entity'])
            order = self.store.find_one('order', msg_data['order_id'])
            customer = self.store.find_one('customer', order['customer_id'])
            products = [self.store.find_one('product', product_id) for product_id in order['product_ids']]
            msg = """Dear {}!
    
    We've just received € {} from you, thank you for your transfer.
    
    Cheers""".format(customer['name'], sum([int(product['price']) for product in products]))

            requests.post('http://msg-service:5000/email', json={
                "to": customer['email'],
                "msg": msg
            })
        except Exception as e:
            log_error(e)

    def subscribe_to_domain_events(self):
        self.store.subscribe('order', 'created', self.order_created)
        self.store.subscribe('billing', 'created', self.billing_created)
        log_info('subscribed to domain events')

    def unsubscribe_from_domain_events(self):
        self.store.unsubscribe('order', 'created', self.order_created)
        self.store.unsubscribe('billing', 'created', self.billing_created)
        log_info('unsubscribed from domain events')


bs = BillingService()

tl = Timeloop()


@tl.job(interval=timedelta(seconds=5))
def rc():
    bs.redis_chk(bs.chk_class, bs.store)


tl.start()

app = Flask(__name__)


@app.route('/billings', methods=['GET'])
@app.route('/billing/<billing_id>', methods=['GET'])
@app.route('/health', methods=['GET'])
@app.route('/ready', methods=['GET'])
@app.route('/restart', methods=['GET'])
def get(billing_id=None):
    if 'health' in request.path:
        if bs.chk_class.restart:
            abort(500)
        else:
            return json.dumps(True)
    elif 'ready' in request.path:
        if bs.chk_resdis_store_bad(bs.chk_class, bs.store):
            abort(503)
        else:
            return json.dumps(True)
    elif 'restart' in request.path:
        bs.chk_class.restart = True
        return json.dumps(True)
    elif billing_id:
        billing = bs.store.find_one('billing', billing_id)
        if not billing:
            raise ValueError("could not find billing")

        return json.dumps(billing) if billing else json.dumps(False)
    else:
        return json.dumps([item for item in bs.store.find_all('billing')])


@app.route('/billing', methods=['POST'])
@app.route('/billings', methods=['POST'])
def post():
    values = request.get_json()
    if not isinstance(values, list):
        values = [values]

    billing_ids = []
    for value in values:
        try:
            new_billing = bs.create_billing(value['order_id'])
        except KeyError:
            raise ValueError("missing mandatory parameter 'order_id'")

        # trigger event
        bs.store.publish('billing', 'created', **new_billing)

        billing_ids.append(new_billing['id'])

    return json.dumps(billing_ids)


@app.route('/billing/<billing_id>', methods=['PUT'])
def put(billing_id):
    value = request.get_json()
    try:
        billing = bs.create_billing(value['order_id'])
    except KeyError:
        raise ValueError("missing mandatory parameter 'order_id'")

    billing['id'] = billing_id

    # trigger event
    bs.store.publish('billing', 'updated', **billing)

    return json.dumps(True)


@app.route('/billing/<billing_id>', methods=['DELETE'])
def delete(billing_id):
    billing = bs.store.find_one('billing', billing_id)
    if billing:

        # trigger event
        bs.store.publish('billing', 'deleted', **billing)

        return json.dumps(True)
    else:
        raise ValueError("could not find billing")
