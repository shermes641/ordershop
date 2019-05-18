import json

from flask import Flask
from flask import request

app = Flask(__name__)


@app.route('/email', methods=['POST'])
def post():
    values = json.loads(request.data)
    if not values['to'] or not values['msg']:
        raise ValueError("missing mandatory parameter 'to' and/or 'msg'")

    app.logger.info('sent email with message "{}" to "{}"'.format(values['msg'], values['to']))
    return json.dumps(True)
