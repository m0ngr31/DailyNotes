import os


basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
  JWT_SECRET_KEY = os.environ.get('API_SECRET_KEY')
  SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or 'sqlite:///' + os.path.join(basedir + '/config', 'app.db')
  SQLALCHEMY_TRACK_MODIFICATIONS = False