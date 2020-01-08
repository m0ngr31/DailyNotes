#!/usr/bin/env python

import platform
import binascii
import os
import os.path

def main():
  if os.path.isfile('./config/.env'):
    return

  SECRET_KEY = os.getenv('API_SECRET_KEY', None)

  if not SECRET_KEY:
    major, minor, patch = platform.python_version_tuple()

    if major is '2':
      SECRET_KEY = "export API_SECRET_KEY=\"{}\"".format(binascii.hexlify(os.urandom(24)))
    elif major is '3':
      SECRET_KEY = "export API_SECRET_KEY=\"{}\"".format(str(binascii.hexlify(os.urandom(24)), "utf-8"))
  else:
    SECRET_KEY = "export API_SECRET_KEY=\"{}\"".format(SECRET_KEY)

  if not os.path.exists('./config'):
    os.makedirs('./config')

  f = open('./config/.env', "w")
  f.write(SECRET_KEY)
  f.close()

main()
