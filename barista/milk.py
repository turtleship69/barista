from quart import Quart, redirect, request, g, session, jsonify
from jwt import PyJWKClient
import jwt

from .beans import inform_new_chat
from .models import User, getUserById, getUserBySessionId
from .tools import gravatar, utc_now, handle_new_chat_request
from .config import AUDIENCE, public_keys

import functools
import sqlite3
import uuid
import os
import re

debug = True

app = Quart(__name__)

if debug:
    app.secret_key = "secret"
else:
    app.secret_key = os.urandom(24).hex()


@app.before_request
async def get_db():
    if "db" not in g:
        g.db = sqlite3.connect("content/database.db")
        g.db.row_factory = sqlite3.Row

    # if session.get("session_id"):
    #     g.user = getUserBySessionId(session.get("session_id"), g.db)
    #     print(g.user)


@app.after_request
async def close_db(response):
    db = g.pop("db", None)
    if db is not None:
        db.commit()
        db.close()
    return response


def login_required(view):
    @functools.wraps(view)
    async def wrapped_view(**kwargs):
        # get session from db
        g.test = 345
        if "session_id" in session:
            g.user = getUserBySessionId(session["session_id"], g.db)
            if not g.user:
                response = {
                    "status": "error",
                    "error": "unauthenticated",
                    "message": "Invalid session",
                }
                return response, 401
        else:
            return {
                "status": "error",
                "error": "unauthenticated",
                "message": "Not logged in",
            }, 401

        if g.user.user_id == g.user.username:
            response = {
                "status": "error",
                "error": "notOnboarded",
                "redirect_url": "/onboarding",
                "message": "User needs to finish signing up at /onboarding",
            }
            return response, 401
        return view(**kwargs)

    return wrapped_view

def async_login_required(view):
    @functools.wraps(view)
    async def wrapped_view(**kwargs):
        # get session from db
        g.test = 345
        if "session_id" in session:
            g.user = getUserBySessionId(session["session_id"], g.db)
            if not g.user:
                response = {
                    "status": "error",
                    "error": "unauthenticated",
                    "message": "Invalid session",
                }
                return response, 401
        else:
            return {
                "status": "error",
                "error": "unauthenticated",
                "message": "Not logged in",
            }, 401

        if g.user.user_id == g.user.username:
            response = {
                "status": "error",
                "error": "notOnboarded",
                "redirect_url": "/onboarding",
                "message": "User needs to finish signing up at /onboarding",
            }
            return response, 401
        return await view(**kwargs)

    return wrapped_view

@app.route("/")
async def hello():
    return "hello"


# session table = sessions(session_id, user_id, time_created: unix time)
@app.route("/auth")
async def login():

    # validate jwt
    jwt_cookie = request.cookies.get("hanko")
    # print(jwt_cookie)
    if not jwt_cookie:  # check that the cookie exists
        return redirect("/")
    try:
        kid = jwt.get_unverified_header(jwt_cookie)["kid"]
        data = jwt.decode(
            str(jwt_cookie),
            public_keys[kid],
            algorithms=["RS256"],
            audience=AUDIENCE,
        )
        #print(data)
    except Exception as e:
        # The JWT is invalid
        print(e)
        return jsonify({"message": "unknown account"})

    # generate session
    session_id = str(uuid.uuid4())
    session["session_id"] = session_id

    # check if user exists
    user = getUserById(data["sub"], g.db)

    new = False if user else True

    if new:
        # create user
        pfp = gravatar(data["email"]["address"])
        print(pfp)
        g.db.execute(
            "INSERT INTO users (user_id, username, pfp) VALUES (?, ?, ?)",
            (data["sub"], data["sub"], pfp),
        )
        user = User(
            user_id=data["sub"],
            username=data["sub"],
            pfp=gravatar(data["email"]["address"]),
        )
        print(user)

    # create session
    g.db.execute(
        "INSERT INTO sessions (session_id, user_id, time_created) VALUES (?, ?, ?)",
        (session_id, user.user_id, utc_now()),
    )

    if new or user.username == user.user_id:
        redirect_url = "/onboarding"
    else: 
        redirect_url = "/app"


    return {"status": "success",
        "session_id": session_id,
        "redirect_url": redirect_url}, 200


valid_username = re.compile(r"^[a-zA-Z0-9.-]{1,20}$")


@app.route("/update_profile", methods=["POST"])
async def update_profile():
    if not session.get("session_id"):
        return {
            "status": "error",
            "error": "unauthenticated",
            "message": "Not logged in",
        }, 401
    g.user = getUserBySessionId(session["session_id"], g.db)
    if not g.user:
        return {
            "status": "error",
            "error": "unauthenticated",
            "message": "Invalid session",
        }, 401

    data = await request.form
    username = data.get("username")
    if not valid_username.match(username):
        return {
            "status": "error",
            "error": "invalidUsername",
            "message": "Invalid username",
        }, 400

    # update db with new username, and bio if not empty
    command = "UPDATE users SET username = ?"
    params = [username]
    if data.get("bio"):
        command += ", bio = ?"
        params.append(data.get("bio"))

    params.append(g.user.user_id)
    g.db.execute(command + " WHERE user_id = ?", params)

    if data.get("onboarding"):
        return redirect("/app?onboarded=true"), 302
    else:
        return {"status": "success"}, 200


# main app
@app.route("/chatlist.json")
@login_required
def chatlist():
    # get all chats where user is a member, and the most recent message
    """return in the format
    [{
        "name": "Alex Jordon",
        "pfp": "/public/account.png",
        "chatId": "b8fc2366-c097-440e-aedf-97428b480193",
        "lastChat": [
            {
                "sender": "Alex",
                "message": "Just finished the report. Do you want to review it before sending?",
                "time": 1609459200
            }
        ]
    }]
    """
    chats = g.db.execute(
    """
SELECT 
    c.chat_id, 
    CASE 
        WHEN c.chat_name IS NOT NULL THEN c.chat_name
        ELSE (
            SELECT GROUP_CONCAT(u2.username, ', ')
            FROM members m2
            JOIN users u2 ON m2.user_id = u2.user_id
            WHERE m2.chat_id = c.chat_id
              AND m2.user_id != cm.user_id
        )
    END AS chat_name, 
    COALESCE(c.chat_photo, u_other.pfp) AS chat_photo, 
    m.message, 
    m.time, 
    CASE 
        WHEN m.author = cm.user_id THEN NULL
        ELSE u.username
    END AS last_sender
FROM 
    chats c
JOIN 
    members cm ON c.chat_id = cm.chat_id
LEFT JOIN (
    SELECT m1.*
    FROM messages m1
    INNER JOIN (
        SELECT chat_id, MAX(time) AS max_time
        FROM messages
        GROUP BY chat_id
    ) latest ON m1.chat_id = latest.chat_id AND m1.time = latest.max_time
) m ON c.chat_id = m.chat_id
LEFT JOIN 
    users u ON m.author = u.user_id
LEFT JOIN (
    SELECT m3.chat_id, u3.pfp
    FROM members m3
    JOIN users u3 ON m3.user_id = u3.user_id
    WHERE m3.user_id != ?
) u_other ON u_other.chat_id = c.chat_id
WHERE 
    cm.user_id = ?
ORDER BY 
    m.time DESC;
        """,
        (g.user.user_id,g.user.user_id,),
    ).fetchall()

    chatlist = []
    for chat in chats:
        chatlist.append(
            {
                "name": chat["chat_name"],
                "pfp": chat["chat_photo"],
                "chatId": chat["chat_id"],
                "lastChat": [
                    {
                        "sender": chat["last_sender"],
                        "message": chat["message"],
                        "time": chat["time"],
                    }
                ],
            }
        )

    return jsonify(chatlist), 200


@app.route("/chats/<chat_id>.json")
@login_required
def chat(chat_id):
    # get all messages in a chat
    """return in the format
    [{
        "sender": "Alex",
        "message": "Just finished the report. Do you want to review it before sending?",
        "time": 1609459200
    }, 
    {
        "sender": None,
        "message": "Just finished the report. Do you want to review it before sending?",
        "time": 1609459200
    }]
    """
    messages = g.db.execute(
        """WITH recent_messages AS (
        SELECT 
            m.message_id,
            m.message,
            m.time,
            m.author,
            m.chat_id
        FROM 
            messages m
        WHERE 
            m.chat_id = ?
        ORDER BY 
            m.time DESC
        LIMIT 25
    )
    SELECT 
        rm.message_id,
        rm.message,
        rm.time,
        CASE 
            WHEN rm.author = ? THEN NULL
            ELSE rm.author
        END AS sender_id,
        rm.chat_id
    FROM 
        recent_messages rm
    WHERE EXISTS (
        SELECT 1
        FROM members mem
        WHERE mem.chat_id = ?
        AND mem.user_id = ?
    )
    ORDER BY rm.time ASC;
""",
        (chat_id, g.user.user_id, chat_id, g.user.user_id),
    ).fetchall()

    messages = [
        {
            "sender": message["sender_id"],
            "message": message["message"],
            "time": message["time"],
        }
        for message in messages
    ]

    return jsonify(messages), 200

@app.route("/new_chat", methods=["POST"])
@async_login_required
async def new_chat():
    # get all messages in a chat
    requested_user_username = (await request.form).get("username")
    print(requested_user_username)
    if not requested_user_username:
        return {
            "status": "error",
            "error": "invalidUsername",
            "message": "Invalid username",
        }, 400

    new_chat = await handle_new_chat_request(
        g.user.user_id, requested_user_username, g.db
    )

    response = {
        "status": new_chat["status"],
        "message": new_chat["message"],
        "pfp": new_chat["pfp"],
        "chatId": new_chat["chat_id"],
    }
    print(new_chat)

    await inform_new_chat(
        new_chat["requested_id"],
        {
            "chat_id": new_chat["chat_id"],
            "pfp": g.user.pfp,
            "name": g.user.username,
        },
    )

    return response, new_chat["status_code"]

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=64390)
