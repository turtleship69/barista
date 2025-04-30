# user table = users(user_id, username, pfp)
# session table = sessions(session_id, user_id, time_created, last_used)
from sqlite3 import Connection
from flask import g

class User():
    def __init__(self, user_id:str = None , username:str = None, pfp:str = None) -> None:
        self.user_id = user_id if user_id else None
        self.username = username if username else None
        self.pfp = pfp if pfp else None

    def __repr__(self) -> str:
        return f"User({self.user_id}, {self.username}, {self.pfp})"



def getUserByQuery(filter: str, value: str, db: Connection) -> User|None:
    
    result = db.execute(f"SELECT * FROM users WHERE {filter}", [value]).fetchone()
    if not result:
        return None
    user = {
        "user_id": result["user_id"],
        "username": result["username"],
        "pfp": result["pfp"]
    }
    return User(user["user_id"], user["username"], user["pfp"])

def getUserById(user_id: str, db: Connection) -> User|None:
    return getUserByQuery("user_id = ?", user_id, db)

def getUserByUsername(username: str, db: Connection) -> User|None:
    return getUserByQuery("username = ?", username, db)

def getUserBySessionId(session_id: str, db: Connection) -> User|None:
    return getUserByQuery("user_id = (SELECT user_id FROM sessions WHERE session_id = ?)", session_id, db)