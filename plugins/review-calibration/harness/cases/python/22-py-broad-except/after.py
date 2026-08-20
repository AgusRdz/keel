def get_timeout(config):
    try:
        return int(config["timeout"])
    except Exception:
        return 30
