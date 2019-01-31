from flask import Flask
import MySQLdb as mysql
import os


app = Flask(__name__)
app.config.from_object('config')
app.secret_key= 'some_secret'
from app import views


