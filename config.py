import json

class Config:
    def __init__(self, config_file):
        fp = open(config_file, 'r')
        self.config = json.load(fp)
        fp.close()

    def get_config(self):
        return self.config
