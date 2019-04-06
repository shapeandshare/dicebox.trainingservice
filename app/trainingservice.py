#!flask/bin/python
###############################################################################
# Training Service
#   Handles requests for training sessions
#
# Copyright (c) 2017-2019 Joshua Burt
###############################################################################


###############################################################################
# Dependencies
###############################################################################
from flask import Flask, jsonify, request, make_response, abort
from flask_cors import CORS, cross_origin
import logging
import uuid
import pika
import json
import os
import errno
from dicebox.config.dicebox_config import DiceboxConfig

# Config
config_file='./dicebox.config'
CONFIG = DiceboxConfig(config_file)


###############################################################################
# Allows for easy directory structure creation
# https://stackoverflow.com/questions/273192/how-can-i-create-a-directory-if-it-does-not-exist
###############################################################################
def make_sure_path_exists(path):
    try:
        if os.path.exists(path) is False:
            os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


###############################################################################
# Setup logging.
###############################################################################
make_sure_path_exists(CONFIG.LOGS_DIR)
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p',
    level=logging.DEBUG,
    filemode='w',
    filename="%s/trainingservice.%s.log" % (CONFIG.LOGS_DIR, os.uname()[1])
)


###############################################################################
# Create the flask, and cors config
###############################################################################
app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "http://localhost:*"}})


###############################################################################
# Handles submission of the actual training request to the message system
###############################################################################
def train_request():
    training_request_id = uuid.uuid4()

    try:
        ## Submit our message
        url = CONFIG.TRAINING_SERVICE_RABBITMQ_URL
        logging.debug(url)
        parameters = pika.URLParameters(url)
        connection = pika.BlockingConnection(parameters=parameters)

        channel = connection.channel()

        channel.queue_declare(queue=CONFIG.TRAINING_SERVICE_RABBITMQ_TRAIN_REQUEST_TASK_QUEUE, durable=True)

        training_request = {}
        training_request['training_request_id'] = str(training_request_id)
        channel.basic_publish(exchange=CONFIG.TRAINING_SERVICE_RABBITMQ_EXCHANGE,
                              routing_key=CONFIG.TRAINING_SERVICE_RABBITMQ_TRAINING_REQUEST_ROUTING_KEY,
                              body=json.dumps(training_request),
                              properties=pika.BasicProperties(
                                  delivery_mode=2,  # make message persistent
                              ))
        logging.debug(" [x] Sent %r" % json.dumps(training_request))
    except:
        # something went wrong..
        training_request_id = None
        logging.error('we had a failure sending the request to the message system')
    finally:
        connection.close()

    return training_request_id


###############################################################################
# Accepts requests for async training sessions
###############################################################################
@app.route('/api/train/request', methods=['GET'])
def make_api_train_request_public():
    if request.headers['API-ACCESS-KEY'] != CONFIG.API_ACCESS_KEY:
        logging.debug('bad access key')
        abort(403)
    if request.headers['API-VERSION'] != CONFIG.API_VERSION:
        logging.debug('bad access version')
        abort(400)
    training_request_id = train_request()
    return make_response(jsonify({'training_request_id': training_request_id}), 202)


###############################################################################
# Returns API version
###############################################################################
@app.route('/api/version', methods=['GET'])
def make_api_version_public():
    return make_response(jsonify({'version':  str(CONFIG.API_VERSION)}), 200)


###############################################################################
# Super generic health end-point
###############################################################################
@app.route('/health/plain', methods=['GET'])
@cross_origin()
def make_health_plain_public():
    return make_response('true', 200)


###############################################################################
# 404 Handler
###############################################################################
@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


###############################################################################
# main entry point, thread safe
###############################################################################
if __name__ == '__main__':
    logging.debug('starting flask app')
    app.run(debug=CONFIG.FLASK_DEBUG, host=CONFIG.LISTENING_HOST, threaded=True)
