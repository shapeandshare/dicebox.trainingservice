#!flask/bin/python
from lib import dicebox_config as config
from lib import sensory_interface
from flask import Flask, jsonify, request, make_response, abort
from flask_cors import CORS, cross_origin
import base64
import logging
import json
from datetime import datetime
import os
import errno
import uuid
import numpy
import pika
#import logging
#import lib.dicebox_config as config
from lib.network import Network
#from datetime import datetime
import json


# Setup logging.
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p',
    level=logging.DEBUG,
    filemode='w',
    filename="%s/training_service.log" % config.LOGS_DIR
)


app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "http://localhost:*"}})


def train_request():
    training_request_id = uuid.uuid4()

    try:
        ## Submit our message
        url = config.TRAINING_SERVICE_RABBITMQ_URL
        logging.debug(url)
        parameters = pika.URLParameters(url)
        connection = pika.BlockingConnection(parameters=parameters)

        channel = connection.channel()

        channel.queue_declare(queue=config.TRAINING_SERVICE_RABBITMQ_TRAIN_REQUEST_TASK_QUEUE, durable=True)

        training_request = {}
        training_request['training_request_id'] = str(training_request_id)
        channel.basic_publish(exchange=config.TRAINING_SERVICE_RABBITMQ_EXCHANGE,
                              routing_key=config.TRAINING_SERVICE_RABBITMQ_TRAINING_REQUEST_ROUTING_KEY,
                              body=json.dumps(training_request),
                              properties=pika.BasicProperties(
                                  delivery_mode=2,  # make message persistent
                              ))
        logging.debug(" [x] Sent %r" % json.dumps(training_request))
        connection.close()
    except:
        # something went wrong..
        logging.error('we had a failure sending the request to the message system')
        return None

    return training_request_id


# for small batches..
@app.route('/api/train/request', methods=['POST'])
def make_api_train_request_public():
    if request.headers['API-ACCESS-KEY'] != config.API_ACCESS_KEY:
        logging.debug('bad access key')
        abort(401)
    if request.headers['API-VERSION'] != config.API_VERSION:
        logging.debug('bad access version')
        abort(400)
    training_request_id = train_request()
    return make_response(jsonify({'training_request_id': training_request_id}), 201)



@app.route('/api/version', methods=['GET'])
def make_api_version_public():
    return make_response(jsonify({'version':  str(config.API_VERSION)}), 201)


@app.route('/health/plain', methods=['GET'])
@cross_origin()
def make_health_plain_public():
    return make_response('true', 201)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


if __name__ == '__main__':
    logging.debug('starting flask app')
    app.run(debug=config.FLASK_DEBUG, host=config.LISTENING_HOST, threaded=True)
