def get_timeout(config):
    try:
        return int(config["timeout"])
    except KeyError:
        return 30
