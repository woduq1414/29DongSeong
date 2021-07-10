import configparser

import os
# from app.common.function import is_local
import json
import socket





scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

# if is_local():
if socket.gethostname()[:7] == "DESKTOP":

    config = configparser.ConfigParser()
    config.read('config.ini')

    pg_db_username = config['DEFAULT']['LOCAL_DB_USERNAME']
    pg_db_password = config['DEFAULT']['LOCAL_DB_PASSWORD']
    pg_db_name = config['DEFAULT']['LOCAL_DB_NAME']
    pg_db_hostname = config['DEFAULT']['LOCAL_DB_HOSTNAME']



    SECRET_KEY = config['DEFAULT']['SECRET_KEY']

    # credentials = ServiceAccountCredentials.from_json_keyfile_name(config['DEFAULT']['GOOGLE_CREDENTIALS_PATH'], scope)

    # DISCORD_WEBHOOK_URL = config["DEFAULT"]["DISCORD_WEBHOOK_URL"]

    # REDIS_URL = config['DEFAULT']['REDIS_URL']


    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True
    SESSION_TYPE = 'redis'


else:


    SECRET_KEY = os.environ.get('SECRET_KEY', None)
    print(os.environ.get('GOOGLE_CREDENTIALS', None))
    print(json.loads(os.environ.get('GOOGLE_CREDENTIALS', None)))
    # credentials = ServiceAccountCredentials.from_json_keyfile_dict(
    #     json.loads(os.environ.get('GOOGLE_CREDENTIALS', None)), scope)


    # DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", None)

    # REDIS_URL = os.environ.get('REDIS_URL', None)


    # SESSION_TYPE = 'redis'
    # SESSION_REDIS = redis.from_url(REDIS_URL)


# SESSION_REDIS = redis.Redis(host=REDIS_URL.split("redis://:")[1].split("@")[1].split(":")[0],
#                                 password=REDIS_URL.split("redis://:")[1].split("@")[0],
#                                 port=REDIS_URL.split("redis://:")[1].split(":")[1])


