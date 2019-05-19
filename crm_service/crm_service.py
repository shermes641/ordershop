import json
import logging
from datetime import timedelta

import requests
from flask import Flask
from flask import request, abort
from timeloop import Timeloop

from common.service_base import ServiceBase
from common.utils import log_error, log_info, ChkClass
from lib.event_store import EventStore


class CrmService(ServiceBase):
    def __init__(self):
        self.chk_class = ChkClass('crm')
        self.store = EventStore(self.chk_class.name)
        self.init_store(self.chk_class, self.store)

    @staticmethod
    def customer_created(item):
        try:
            msg_data = json.loads(item[1][0][1]['entity'])
            msg = """Dear {}!
    
    Welcome to Ordershop.
    
    Cheers""".format(msg_data['name'])
            log_info(msg)
            requests.post('http://msg-service:5000/email', json={
                "to": msg_data['email'],
                "msg": msg
            })
        except Exception as e:
            log_error(e)

    @staticmethod
    def customer_deleted(item):
        try:
            msg_data = json.loads(item[1][0][1]['entity'])
            msg = """Dear {}!
    
    Good bye, hope to see you soon again at Ordershop.
    
    Cheers""".format(msg_data['name'])
            log_info(msg)
            requests.post('http://msg-service:5000/email', json={
                "to": msg_data['email'],
                "msg": msg
            })
        except Exception as e:
            log_info('CRM DELETE EXCEPTION')
            log_error(e)

    def order_created(self, item):
        try:
            msg_data = json.loads(item[1][0][1]['entity'])
            customer = self.store.find_one('customer', msg_data['customer_id'])
            products = [self.store.find_one('product', product_id) for product_id in msg_data['product_ids']]
            msg = """Dear {}!
    
    Thank you for buying following {} products from Ordershop:
    {}
    
    Cheers""".format(customer['name'], len(products), ", ".join([product['name'] for product in products]))
            log_info(msg)
            requests.post('http://msg-service:5000/email', json={
                "to": customer['email'],
                "msg": msg
            })
        except Exception as e:
            log_error(e)

    def subscribe_to_domain_events(self):
        self.store.subscribe('customer', 'created', self.customer_created)
        self.store.subscribe('customer', 'deleted', self.customer_deleted)
        self.store.subscribe('order', 'created', self.order_created)

    def unsubscribe_from_domain_events(self):
        self.store.unsubscribe('customer', 'created', self.customer_created)
        self.store.unsubscribe('customer', 'deleted', self.customer_deleted)
        self.store.unsubscribe('order', 'created', self.order_created)


crm = CrmService()

tl = Timeloop()


@tl.job(interval=timedelta(seconds=5))
def rc():
    crm.redis_chk(crm.chk_class, crm.store)


tl.start()

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(crm.chk_class.service.LOGLEVEL)

@app.route('/health', methods=['GET'])
@app.route('/ready', methods=['GET'])
@app.route('/restart', methods=['GET'])
def get():
    if 'health' in request.path:
        if crm.chk_class.restart:
            abort(500)
        else:
            return json.dumps(True)
    elif 'ready' in request.path:
        if crm.chk_redis_store_bad(crm.chk_class, crm.store):
            abort(503)
        else:
            return json.dumps(True)
    elif 'restart' in request.path:
        crm.chk_class.restart = True
        return json.dumps(True)
    else:
        return json.dumps(False)
