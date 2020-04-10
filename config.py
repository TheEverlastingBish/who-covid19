import os
import json
from configparser import ConfigParser


class AppConfig:
    """ Interact with configuration variables and methods"""

    configParser = ConfigParser()

    URL = r"https://www.who.int/emergencies/diseases/novel-coronavirus-2019/situation-reports"

    repo_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(repo_dir, 'data')

    bad_rows = ['Subtotal for all', 'regions', 'Grand total', 'International', 'conveyance (Diamond']

    with open(os.path.join(repo_dir, 'replacements.json')) as read_file:
        data_columns = json.load(read_file)

    @classmethod
    def setup_dirs(cls, data_dir=data_dir):
        if not os.path.exists(data_dir):
            os.mkdir(data_dir)

    @classmethod
    def initialize(cls):
        cls.setup_dirs()

