import json
import uuid
from datetime import timedelta

from flask import Flask
from flask import request, abort
from timeloop import Timeloop

from common.service_base import ServiceBase
from common.utils import ChkClass
from lib.event_store import EventStore


class ProductService(ServiceBase):
    def __init__(self):
        self.chk_class = ChkClass('product')
        self.store = EventStore(self.chk_class.name)
        self.init_store(self.chk_class, self.store)

    @staticmethod
    def create_product(_name, _price):
        """
        Create a product entity.

        :param _name: The name of the product.
        :param _price: The price of the product.
        :return: A dict with the entity properties.
        """
        return {
            'id': str(uuid.uuid4()),
            'name': _name,
            'price': _price
        }


prods = ProductService()

tl = Timeloop()


@tl.job(interval=timedelta(seconds=5))
def rc():
    prods.redis_chk(prods.chk_class, prods.store)


tl.start()

app = Flask(__name__)


@app.route('/products', methods=['GET'])
@app.route('/product/<product_id>', methods=['GET'])
@app.route('/health', methods=['GET'])
@app.route('/ready', methods=['GET'])
@app.route('/restart', methods=['GET'])
def get(product_id=None):
    if 'health' in request.path:
        if prods.chk_class.restart:
            abort(500)
        else:
            return json.dumps(True)
    elif 'ready' in request.path:
        if prods.chk_resdis_store_bad(prods.chk_class, prods.store):
            abort(503)
        else:
            return json.dumps(True)
    elif 'restart' in request.path:
        prods.chk_class.restart = True
        return json.dumps(True)
    elif product_id:
        product = prods.store.find_one('product', product_id)
        if not product:
            raise ValueError("could not find product")

        return json.dumps(product) if product else json.dumps(False)
    else:
        return json.dumps([item for item in prods.store.find_all('product')])


@app.route('/product', methods=['POST'])
@app.route('/products', methods=['POST'])
def post():
    values = request.get_json()
    if not isinstance(values, list):
        values = [values]

    product_ids = []
    for value in values:
        try:
            new_product = prods.create_product(value['name'], value['price'])
        except KeyError:
            raise ValueError("missing mandatory parameter 'name' and/or 'price'")

        # trigger event
        prods.store.publish('product', 'created', **new_product)

        product_ids.append(new_product['id'])

    return json.dumps(product_ids)


@app.route('/product/<product_id>', methods=['PUT'])
def put(product_id):
    value = request.get_json()
    try:
        product = prods.create_product(value['name'], value['price'])
    except KeyError:
        raise ValueError("missing mandatory parameter 'name' and/or 'price'")

    product['id'] = product_id

    # trigger event
    prods.store.publish('product', 'updated', **product)

    return json.dumps(True)


@app.route('/product/<product_id>', methods=['DELETE'])
def delete(product_id):
    product = prods.store.find_one('product', product_id)
    if product:

        # trigger event
        prods.store.publish('product', 'deleted', **product)

        return json.dumps(True)
    else:
        raise ValueError("could not find product")
