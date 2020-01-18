#!/usr/bin/env python

import platform
import binascii
import os
import os.path

def main():
  # Already have env setup
  if os.path.isfile('./config/.env'):
    return

  # Don't need to create config folder if env vars are already set
  if os.getenv('API_SECRET_KEY', None) and os.getenv('DATABASE_URI', None):
    return

  API_SECRET_KEY = os.getenv('API_SECRET_KEY', None)

  if not API_SECRET_KEY:
    major, minor, patch = platform.python_version_tuple()

    if major == '2':
      SECRET_KEY = "export API_SECRET_KEY=\"{}\"".format(binascii.hexlify(os.urandom(24)))
    elif major == '3':
      SECRET_KEY = "export API_SECRET_KEY=\"{}\"".format(str(binascii.hexlify(os.urandom(24)), "utf-8"))
  else:
    SECRET_KEY = "export API_SECRET_KEY=\"{}\"".format(API_SECRET_KEY)

  if not os.path.exists('./config'):
    os.makedirs('./config')

  f = open('./config/.env', "w")
  f.write(SECRET_KEY)
  f.close()

main()
