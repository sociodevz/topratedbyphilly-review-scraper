import json
import os

config = {}
dir_path = os.path.dirname(os.path.realpath(__file__))

with open(f'{dir_path}/config.json', 'r') as config_file:
    config.update(json.load(config_file))

def updateConfigFromArgs(args):
    other_args = []
    for arg in args:
        k, v = arg.split('=') if '=' in arg else (None, None)
        if k in config:
            if isinstance(config[k], int):
                config[k] = int(v)
            else:
                config[k] = v
        else:
            other_args.append(arg)

    return other_args
