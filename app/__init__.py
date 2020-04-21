from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_argon2 import Argon2


app = Flask(__name__,
  static_url_path='/static',
  static_folder = "../dist/static",
  template_folder = "../dist"
)

app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)
argon2 = Argon2(app)

from app import routes, models
