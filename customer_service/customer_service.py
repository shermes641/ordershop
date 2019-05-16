import atexit
import json
import os
import uuid

from common.utils import log_info, log_error

from flask import request, abort
from flask import Flask

from lib.event_store import EventStore


app = Flask(__name__)
store = EventStore()


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


if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    store.activate_entity_cache('customer')
    atexit.register(store.deactivate_entity_cache, 'customer')

restart = False

@app.route('/customers', methods=['GET'])
@app.route('/customer/<customer_id>', methods=['GET'])
@app.route('/health', methods=['GET'])
@app.route('/restart', methods=['GET'])
def get(customer_id=None):
    global restart
    if 'health' in request.path:
        if restart:
            abort(500)
        else:
            return json.dumps(True)
    elif 'restart' in request.path:
        restart = True
        return json.dumps(True)
    elif customer_id:
        customer = store.find_one('customer', customer_id)
        if not customer:
            raise ValueError("could not find customer")

        return json.dumps(customer) if customer else json.dumps(False)
    else:
        return json.dumps([item for item in store.find_all('customer')])


@app.route('/customer', methods=['POST'])
@app.route('/customers', methods=['POST'])
def post():

    values = request.get_json()
    if not isinstance(values, list):
        values = [values]

    customer_ids = []
    for value in values:
        log_info('CREATE CUST')
        log_info(value)
        try:
            new_customer = create_customer(value['name'], value['email'])
        except KeyError:
            raise ValueError("missing mandatory parameter 'name' and/or 'email'")

        # trigger event
        store.publish('customer', 'created', **new_customer)

        customer_ids.append(new_customer['id'])

    return json.dumps(customer_ids)


@app.route('/customer/<customer_id>', methods=['PUT'])
def put(customer_id):

    value = request.get_json()
    log_info('PUT CUST')
    log_info(customer_id)
    log_info(value)
    try:
        customer = create_customer(value['name'], value['email'])
    except KeyError:
        raise ValueError("missing mandatory parameter 'name' and/or 'email'")

    customer['id'] = customer_id

    # trigger event
    store.publish('customer', 'updated', **customer)

    return json.dumps(True)


@app.route('/customer/<customer_id>', methods=['DELETE'])
def delete(customer_id):

    log_info('DELETE CUST')
    log_info(customer_id)

    customer = store.find_one('customer', customer_id)
    log_info(customer)
    if customer:
        log_info('PUBLISH DELETE CUST')
        # trigger event
        store.publish('customer', 'deleted', **customer)

        return json.dumps(True)
    else:
        log_info('DELETE CUST NOT FOUND')
        raise ValueError("could not find customer")

