import json
import os
import uuid

from flask import Flask
from flask import request, abort

from common.service_base import ServiceBase
from common.utils import ChkClass
from lib.event_store import EventStore


class CustomerService(ServiceBase):
    def __init__(self, logger):
        self.log = logger
        self.chk_class = ChkClass('customer')
        self.store = EventStore(self.chk_class.name)
        super().__init__(self.chk_class, self.store, self.log)


def create_customer(_name, _email):
    """
    Create a customer entity.

    :param _name: The name of the customer.
    :param _email: The email address of the customer.
    :return: A dict with the entity properties.
    """
    return {
        'id': str(uuid.uuid4()),
        'name': _name,
        'email': _email
    }


app = Flask(__name__)
app.logger.setLevel(os.getenv('LOGLEVEL'))
cs = CustomerService(app.logger)

@app.route('/customers', methods=['GET'])
@app.route('/customer/<customer_id>', methods=['GET'])
@app.route('/health', methods=['GET'])
@app.route('/ready', methods=['GET'])
@app.route('/restart', methods=['GET'])
def get(customer_id=None):
    if cs.service_error():
        abort(503)

    if 'health' in request.path:
        if cs.chk_class.restart:
            abort(500)
        else:
            return json.dumps(True)
    elif 'ready' in request.path:
        return json.dumps(True)
    elif 'restart' in request.path:
        cs.chk_class.restart = True
        return json.dumps(True)
    elif customer_id:
        customer = cs.store.find_one('customer', customer_id)
        if not customer:
            raise ValueError("could not find customer")

        return json.dumps(customer) if customer else json.dumps(False)
    else:
        return json.dumps([item for item in cs.store.find_all('customer')])


@app.route('/customer', methods=['POST'])
@app.route('/customers', methods=['POST'])
def post():
    values = request.get_json()
    if not isinstance(values, list):
        values = [values]

    customer_ids = []
    for value in values:
        try:
            new_customer = create_customer(value['name'], value['email'])
        except KeyError:
            raise ValueError("missing mandatory parameter 'name' and/or 'email'")

        # trigger event
        cs.store.publish('customer', 'created', **new_customer)

        customer_ids.append(new_customer['id'])

    return json.dumps(customer_ids)


@app.route('/customer/<customer_id>', methods=['PUT'])
def put(customer_id):
    value = request.get_json()
    try:
        customer = create_customer(value['name'], value['email'])
    except KeyError:
        raise ValueError("missing mandatory parameter 'name' and/or 'email'")

    customer['id'] = customer_id

    # trigger event
    cs.store.publish('customer', 'updated', **customer)

    return json.dumps(True)


@app.route('/customer/<customer_id>', methods=['DELETE'])
def delete(customer_id):
    customer = cs.store.find_one('customer', customer_id)
    if customer:
        # trigger event
        cs.store.publish('customer', 'deleted', **customer)

        return json.dumps(True)
    else:
        raise ValueError("could not find customer")
