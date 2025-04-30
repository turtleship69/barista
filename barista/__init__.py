from .milk import app
from .beans import sio

import socketio
import sqlite3

app = socketio.ASGIApp(sio, app)


#check database exists, otherwise create it

with open("content/database.sql") as f:
    SCHEMA = f.read()

db = sqlite3.connect("content/database.db")
db.row_factory = sqlite3.Row
db.executescript(SCHEMA)