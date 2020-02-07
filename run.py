import requests
import yaml
import os

def get_operation(method):
    method = method.lower()
    if hasattr(requests, method): 
        operation = getattr(requests, method)
    else:
        raise AttributeError(f'Not existing method file {method}')
    return operation

def do_call(configuration):
    method = configuration.get('method', 'get')
    operation = get_operation(method)

    url = configuration.get('url', None)
    if url is None:
        raise AttributeError('No url defined')

    options = {}
    options['params'] = configuration.get('params', None)
    options['headers'] = configuration.get('headers', None)
    options['data'] = configuration.get('data', None)
    options['auth'] = configuration.get('auth', None)

    print(f"Calling: {method} {url}")
    response = operation(url, **options)
    return response


config = os.environ.get('CONFIG_FILE', 'config.yaml')

if os.path.exists(config):
    with open(config, 'r') as config_file:
        yaml_configuration = yaml.load(config_file.read(), Loader=yaml.SafeLoader)
else:
    raise AttributeError(f'Not existing config file {config}')

# WAIT FOR
wait_for = yaml_configuration.get('wait_for')

if wait_for is not None:
    response = do_call(wait_for)
    expected_status = wait_for.get('status')
    intents = wait_for.get('intents')
    wait_time = wait_for.get('wait')

    if response.status_code != expected_status and intents > 0:
        time.sleep(wait_time)
        response = do_call(wait_for)
        intents -= 1


for config_element in yaml_configuration.get('sequencial', []):
    response = do_call(config_element)

    response.raise_for_status()
    print("######## RESPONSE #########")
    print(response.content)
    print("######## END #########")
    print("\n")
