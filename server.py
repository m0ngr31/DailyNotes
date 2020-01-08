# from flask import Flask, request, jsonify, abort, make_response, render_template
# from flask_sqlalchemy import SQLAlchemy

# import logging
# import os


# app = Flask(__name__,
#   static_url_path='/static',
#   static_folder = "./dist/static",
#   template_folder = "./dist"
# )
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///config/app.db'
# db = SQLAlchemy(app)

# class User(db.Model):
#   id = db.Column(db.)




# # Main
# if __name__ != '__main__':
#   gunicorn_logger = logging.getLogger('gunicorn.error')
#   app.logger.handlers = gunicorn_logger.handlers
#   app.logger.setLevel(gunicorn_logger.level)


# if __name__ == '__main__':
#   debug = os.environ.get('DEVELOP', False)
#   app.run(debug=debug)

from app import app