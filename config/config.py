
import os
import sys
import yaml


def last_config_fil(config_file):
    if config_file:
        if not os.path.exists(config_file):
            # log.error("Config file was not found..")
            sys.exit(1)
        try:
            with open(config_file, 'r') as f:
                cfg = yaml.load(f, Loader=yaml.BaseLoader)
        except yaml.scanner.ScannerError as se:
            sys.exit(1)

    return cfg
