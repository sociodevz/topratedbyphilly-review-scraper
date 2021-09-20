config = {
    'debug': True,
    'logger_severity_level': 'ERROR',
    'chrome_headless_mode': True,
    'project_physical_root_path': '/var/www/html/topratedbyphilly/scraper/',
    'scraper_mode': 'online',
    'proxy_url_ip': '63.141.236.210:19016',
    'proxy_enabled': True,
    'scraper_sites': 'yelp,bbb,trustpilot,houzz,googlemaps,buildzoom,angi,gaf,bestpickreports'
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
