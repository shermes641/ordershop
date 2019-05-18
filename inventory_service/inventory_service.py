import json
import uuid
from datetime import timedelta

from flask import Flask
from flask import request, abort
from timeloop import Timeloop

from common.service_base import ServiceBase
from common.utils import ChkClass
from lib.event_store import EventStore


class InventoryService(ServiceBase):
    def __init__(self):
        self.chk_class = ChkClass('inventory')
        self.store = EventStore(self.chk_class.name)
        self.init_store(self.chk_class, self.store)

    @staticmethod
    def create_inventory(_product_id, _amount):
        """
        Create an inventory entity.

        :param _product_id: The product ID the inventory is for.
        :param _amount: The amount of products in the inventory.
        :return: A dict with the entity properties.
        """
        return {
            'id': str(uuid.uuid4()),
            'product_id': _product_id,
            'amount': _amount
        }


invs = InventoryService()

tl = Timeloop()


@tl.job(interval=timedelta(seconds=5))
def rc():
    invs.redis_chk(invs.chk_class, invs.store)


tl.start()

app = Flask(__name__)


@app.route('/inventory', methods=['GET'])
@app.route('/inventory/<inventory_id>', methods=['GET'])
@app.route('/health', methods=['GET'])
@app.route('/ready', methods=['GET'])
@app.route('/restart', methods=['GET'])
def get(inventory_id=None):
    if 'health' in request.path:
        if invs.chk_class.restart:
            abort(500)
        else:
            return json.dumps(True)
    elif 'ready' in request.path:
        if invs.chk_resdis_store_bad(invs.chk_class, invs.store):
            abort(503)
        else:
            return json.dumps(True)
    elif 'restart' in request.path:
        invs.chk_class.restart = True
        return json.dumps(True)
    elif inventory_id:
        inventory = invs.store.find_one('inventory', inventory_id)
        if not inventory:
            raise ValueError("could not find inventory")

        return json.dumps(inventory) if inventory else json.dumps(False)
    else:
        return json.dumps([item for item in invs.store.find_all('inventory')])


@app.route('/inventory', methods=['POST'])
def post():
    values = request.get_json()
    if not isinstance(values, list):
        values = [values]

    inventory_ids = []
    for value in values:
        try:
            new_inventory = invs.create_inventory(value['product_id'], value['amount'])
        except KeyError:
            raise ValueError("missing mandatory parameter 'product_id' and/or 'amount'")

        # trigger event
        invs.store.publish('inventory', 'created', **new_inventory)

        inventory_ids.append(new_inventory['id'])

    return json.dumps(inventory_ids)


@app.route('/inventory/<inventory_id>', methods=['PUT'])
def put(inventory_id):
    value = request.get_json()
    try:
        inventory = invs.create_inventory(value['product_id'], value['amount'])
    except KeyError:
        raise ValueError("missing mandatory parameter 'name' and/or 'price'")

    inventory['id'] = inventory_id

    # trigger event
    invs.store.publish('inventory', 'updated', **inventory)

    return json.dumps(True)


@app.route('/inventory/<inventory_id>', methods=['DELETE'])
def delete(inventory_id):
    inventory = invs.store.find_one('inventory', inventory_id)
    if inventory:

        # trigger event
        invs.store.publish('inventory', 'deleted', **inventory)

        return json.dumps(True)
    else:
        raise ValueError("could not find inventory")


@app.route('/incr/<product_id>', methods=['POST'])
@app.route('/incr/<product_id>/<value>', methods=['POST'])
def incr(product_id, value=None):
    inventory = list(filter(lambda x: x['product_id'] == product_id, invs.store.find_all('inventory')))
    if not inventory:
        raise ValueError("could not find inventory")

    inventory = inventory[0]
    inventory['amount'] = int(inventory['amount']) - (value if value else 1)

    # trigger event
    invs.store.publish('inventory', 'updated', **inventory)

    return json.dumps(True)


@app.route('/decr/<product_id>', methods=['POST'])
@app.route('/decr/<product_id>/<value>', methods=['POST'])
def decr(product_id, value=None):
    inventory = list(filter(lambda x: x['product_id'] == product_id, invs.store.find_all('inventory')))
    if not inventory:
        raise ValueError("could not find inventory")

    inventory = inventory[0]
    if int(inventory['amount']) - (value if value else 1) >= 0:

        inventory['amount'] = int(inventory['amount']) - (value if value else 1)

        # trigger event
        invs.store.publish('inventory', 'updated', **inventory)

        return json.dumps(True)
    else:
        return json.dumps(False)


@app.route('/decr_from_order', methods=['POST'])
def decr_from_order():
    values = request.get_json()
    if not isinstance(values, list):
        values = [values]

    occurs = {}
    for value in values:
        try:
            product_ids = value['product_ids']
        except KeyError:
            raise ValueError("missing mandatory parameter 'product_ids'")

        for inventory in invs.store.find_all('inventory'):

            if not inventory['product_id'] in occurs:
                occurs[inventory['product_id']] = 0

            occurs[inventory['product_id']] += product_ids.count(inventory['product_id'])
            if occurs[inventory['product_id']] <= int(inventory['amount']):
                continue
            else:
                return json.dumps(False)

    for k, v in occurs.items():
        inventory = list(filter(lambda x: x['product_id'] == k, invs.store.find_all('inventory')))
        if not inventory:
            raise ValueError("could not find inventory")

        inventory = inventory[0]
        if int(inventory['amount']) - v >= 0:

            inventory['amount'] = int(inventory['amount']) - v

            # trigger event
            invs.store.publish('inventory', 'updated', **inventory)

        else:
            return json.dumps(False)

    return json.dumps(True)
