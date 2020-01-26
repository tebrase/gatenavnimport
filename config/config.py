
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


class Config:
    def __init__(self, filename):
        self.config_file = filename
        self.config = last_config_fil(filename)


    def modules(self):
        return self.config.keys()

    def module_props(self, module_name):
        return self.config.get(module_name, {}).keys()

    def get(self, module_name, property_name):
        return self.config.get(module_name, {}).get(property_name, None)

    def get_module(self, module_name):
        return self.config.get(module_name, {})