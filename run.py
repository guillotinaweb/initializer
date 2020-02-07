import requests
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import yaml
import os
import time
import logging

DEFAULT_RETRIES = 2
DEFAULT_BACKOFF = 0.1

logger = logging.getLogger("initializer")
logger.setLevel('INFO')

def get_operation(session, method):
    method = method.lower()
    if hasattr(session, method): 
        operation = getattr(session, method)
    else:
        raise AttributeError(f'Not existing method file {method}')
    return operation

def do_call(session, configuration):
    method = configuration.get('method', 'get')
    operation = get_operation(session, method)

    url = configuration.get('url', None)
    if url is None:
        raise AttributeError('No url defined')

    retries = configuration.get('retries', DEFAULT_RETRIES)
    backoff = configuration.get('backoff', DEFAULT_BACKOFF)

    retries_obj = Retry(
        total=retries,
        connect=retries,
        read=retries,
        backoff_factor=backoff,
        status_forcelist=[ 500, 502, 503, 504 ]
    )
    session.mount(url, HTTPAdapter(max_retries=retries))

    options = {}
    options['params'] = configuration.get('params', None)
    options['headers'] = configuration.get('headers', None)
    options['data'] = configuration.get('data', None)
    options['json'] = configuration.get('json', None)

    auth = configuration.get('auth', None)
    if auth is not None:
        options['auth'] = HTTPBasicAuth(auth[0], auth[1])

    logger.info(f"Calling: {method} {url}")
    try:
        response = operation(url, **options)
    except requests.exceptions.ConnectionError:
        logging.warning(f"No connection to {url}")
        return None
    return response


config = os.environ.get('CONFIG_FILE', 'config.yaml')

if os.path.exists(config):
    with open(config, 'r') as config_file:
        yaml_configuration = yaml.load(config_file.read(), Loader=yaml.SafeLoader)
else:
    raise AttributeError(f'Not existing config file {config}')

session = requests.Session()

# WAIT FOR
wait_for = yaml_configuration.get('wait_for')

if wait_for is not None:
    response = do_call(session, wait_for)

    expected_status = wait_for.get('status', 200)
    retries = wait_for.get('retries', 3)
    wait_time = wait_for.get('wait', 10)

    if (response is None or response.status_code != expected_status) and retries > 0:
        time.sleep(wait_time)
        response = do_call(session, wait_for)
        retries -= 1

    if response is None:
        raise Exception(f"Could not connect")
    
    if response.status_code != expected_status:
        raise Exception(f"Could not get status {expected_status}")


# MAIN LOOP

for config_element in yaml_configuration.get('sequencial', []):
    response = do_call(session, config_element)

    valid = config_element.get('valid', [200, 201])

    if response.status_code not in valid:
        logger.error(response.content)
        raise Exception(f"Expecting {valid} got {response.status_code}")

    logger.info("######## RESPONSE #########")
    logger.info(response.content)
    logger.info("######## END #########")
    logger.info("\n")
