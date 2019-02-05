import os
import sys
import logging

logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, "/home/upzpana1/TA")


from app import app as application
application.secret_key = 'cobacobacoba'

