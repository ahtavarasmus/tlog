import json

with open('/etc/tlog_config.json') as config_file:
    config = json.load(config_file)

class Config(object):
    SECRET_KEY = config.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = config.get('SQLALCHEMY_DATABASE_URI')
    GMAIL_USER = config.get('GMAIL_USER')
    GMAIL_PASSWORD = config.get('GMAIL_PASSWORD')
