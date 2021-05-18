config = {
    'scraper_mode': 'online',
}

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
