import requests
import yaml
import os

config = os.environ.get('CONFIG_FILE', 'config.yaml')

if os.path.exists(config):
    with open(config, 'r') as config_file:
        yaml_configuration = yaml.load(config_file.read())
else:
    raise AttributeError(f'Not existing config file {config}')

for config_element in yaml_configuration.get('sequencial', []):
    method = config_element.get('method', 'get').lower()
    if hasattr(requests, method): 
        operation = getattr(requests, method)
    else:
        raise AttributeError(f'Not existing method file {method}')

    url = config_element.get('url', None)
    if url is None:
        raise AttributeError('No url defined')

    options = {}
    options['params'] = config_element.get('params', None)
    options['headers'] = config_element.get('headers', None)
    options['data'] = config_element.get('data', None)
    options['auth'] = config_element.get('auth', None)

    print(f"Calling: {method} {url}")
    response = operation(url, **options)

    response.raise_for_status()
    print("######## RESPONSE #########")
    print(response.content)
    print("######## END #########")
    print("\n")
