import logging
import lib.dicebox_config as config
from lib.network import Network
from datetime import datetime
import json

# Setup logging.
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p',
    level=logging.DEBUG,
    filemode='w',
    filename="%s/lonestar_train.log" % config.LOGS_DIR
)


def main():
    network = Network(config.NN_PARAM_CHOICES)
    if config.LOAD_BEST_WEIGHTS_ON_START is True:
        logging.info('attempting to restart training from previous session..')
        network.create_lonestar(create_model=True,
                                weights_filename="%s/%s" % (config.WEIGHTS_DIR, config.MODEL_WEIGHTS_FILENAME))
    else:
        network.create_lonestar(create_model=True)

    with open('./category_map.json', 'w') as category_mapping_file:
        category_mapping_file.write(json.dumps(network.fsc.CATEGORY_MAP))

    i = 1
    while i <= config.EPOCHS:
        logging.info("epoch (%i of %i)" % (i, config.EPOCHS))
        network.train_and_save(config.DATASET)

        # save the model after every epoch, regardless of accuracy.
        filename = "%s/weights.epoch_%i.final.%s.hdf5" % (config.WEIGHTS_DIR, i, datetime.now().strftime('%Y-%m-%d_%H_%M_%S_%f'))
        logging.info("saving model weights after epoch %i to file %s" % (i, filename))
        network.save_model(filename)

        # the next epoch..
        i += 1

    logging.info("network accuracy: %.2f%%" % (network.accuracy * 100))
    logging.info('-'*80)
    network.print_network()

if __name__ == '__main__':
    main()
