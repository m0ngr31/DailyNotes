from flask import Flask, request, jsonify, abort, make_response, render_template

import logging
import os


app = Flask(__name__,
  static_url_path='/static',
  static_folder = "./dist/static",
  template_folder = "./dist"
)


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
  return render_template("index.html")


# Main
if __name__ != '__main__':
  gunicorn_logger = logging.getLogger('gunicorn.error')
  app.logger.handlers = gunicorn_logger.handlers
  app.logger.setLevel(gunicorn_logger.level)


if __name__ == '__main__':
  debug = os.environ.get('DEVELOP', False)
  app.run(debug=debug)
