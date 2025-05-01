import uuid
import socketio
import aiosqlite

from .tools import utc_now
from .config import app_url

# create a Socket.IO server
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins=app_url)

global connected_users
connected_users = {}


@sio.event
async def connect(sid, environ, auth):
    print(auth)
    async with aiosqlite.connect("content/database.db") as db:
        db.row_factory = aiosqlite.Row
        # get all auth codes from db
        token = auth.get("token")
        cursor = await db.execute(
            "SELECT * FROM sessions WHERE session_id = ?", (token,)
        )
        rows = await cursor.fetchone()
        if not rows:
            print("No auth code found")
            raise ConnectionRefusedError("authentication failed")

        connected_users[sid] = rows["user_id"]

    print("connect ", sid)


@sio.event
def disconnect(sid):
    print("disconnect ", sid)


@sio.event
async def message(sid, data):
    print("message ", connected_users[sid], data)
    # print(sio.rooms(sid))

    message_id = str(uuid.uuid4())
    message = data.get("message")
    time = utc_now()
    user = connected_users[sid]
    chat_id = data.get("chat_id")

    # todo: verify all data is present

    await sio.emit(
        "incoming_message", {"message": message, "sender": user}, 
        room=chat_id, skip_sid=sid
    )

    async with aiosqlite.connect("content/database.db") as db:
        db.row_factory = aiosqlite.Row
        await db.execute(
            "INSERT INTO messages (message_id, message, time, author, chat_id) VALUES (?, ?, ?, ?, ?)",
            (message_id, message, time, user, chat_id),
        )
        await db.commit()
        # print(f"Message {message_id} sent by {user} in chat {chat_id}.")

    await sio.send("Hello from the server!", to=sid)


@sio.event
async def connect_to_chat(sid, data):
    print("connect_to_chat ", sid, data)
    await sio.enter_room(sid, data)
    await sio.send(f"Joined room {data}", to=sid)
