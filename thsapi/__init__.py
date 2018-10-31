from flask import Flask

app = Flask(__name__)
try:
    app.config.from_pyfile('../config.cfg', silent=True)
except:
    pass

from thsapi import views

