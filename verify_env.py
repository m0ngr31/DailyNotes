#!/usr/bin/env python

import random
import string
import os
import os.path


def gen_random(str_len):
  return ''.join(random.choice(string.hexdigits) for x in range(str_len))


def main():
  # Don't need to create config folder if env vars are already set
  if os.getenv('API_SECRET_KEY', None) and os.getenv('DATABASE_URI', None) and os.getenv('DB_ENCRYPTION_KEY'):
    return

  API_SECRET_KEY = os.getenv('API_SECRET_KEY', None)
  ENCRYPTION_KEY = os.getenv('DB_ENCRYPTION_KEY', None)

  if not API_SECRET_KEY:
    SECRET_KEY = "export API_SECRET_KEY=\"{}\"".format(gen_random(48))
  else:
    SECRET_KEY = "export API_SECRET_KEY=\"{}\"".format(API_SECRET_KEY)

  if not ENCRYPTION_KEY:
    ENCRYPTION_KEY = "export DB_ENCRYPTION_KEY=\"{}\"".format(gen_random(16))
  else:
    ENCRYPTION_KEY = "export DB_ENCRYPTION_KEY=\"{}\"".format(ENCRYPTION_KEY)

  if not os.path.isdir('./config'):
    os.makedirs('./config')

  f = open('./config/.env', "w")
  f.writelines([SECRET_KEY, "\n", ENCRYPTION_KEY])
  f.close()

main()
