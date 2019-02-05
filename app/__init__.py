from flask import Flask,g
import MySQLdb as mysql
import os



app = Flask(__name__)
app.config.from_object('config')
app.secret_key= 'some_secret'
from app import views




@app.before_request
def db_connect():
    g.con = mysql.connect(
        host = "localhost",
        user = "root",
        passwd = "ALFIAN123",
        db = "db_fcm",
        charset = 'utf8',
        use_unicode = True
    )
    g.cursor = g.con.cursor()

@app.after_request
def db_disconnect(response):
    g.cursor.close()
    g.con.close()
    return response
