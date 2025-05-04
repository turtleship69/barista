import hashlib
import time
import uuid


def gravatar(email: str) -> str:
    """
    Generate a Gravatar URL for the given email address.

    Args:
        email (str): The email address to generate the Gravatar for.

    Returns:
        str: The URL of the Gravatar image.
    """
    # Convert the email to a hash using MD5
    email_hash = hashlib.md5(email.lower().encode("utf-8")).hexdigest()

    # Build the Gravatar URL
    url = f"https://www.gravatar.com/avatar/{email_hash}"

    return url


def utc_now():
    return int(time.time())


async def handle_new_chat_request(current_user, requested_user_username, db):
    """
    Handle a new chat request between two users.

    Args:
        current_user (str): The user initiating the chat.
        requested_user (str): The username of the user being requested for a chat.
        db (DatabaseConnection): The database connection object.

    Returns:
        str: A message indicating the result of the operation.
    """
    # TABLE "members" ("chat_id", "user_id")
    # TABLE "chats" ("chat_id", "chat_name", "chat_photo", "isGroup")
    # TABLE "users" ("user_id", "username", "pfp", "bio")
    # Get userid of user and check if the chat already exists
    print(4)
    cursor = db.cursor()
    cursor.execute(
        "SELECT user_id, pfp FROM users WHERE username = ?", (requested_user_username,)
    )
    requested_user = cursor.fetchone()
    if not requested_user:
        return {"status": "error", "message": "User not found", "status_code": 404}

    requested_user_id = requested_user["user_id"]
    cursor.execute(
        "SELECT chat_id FROM members WHERE user_id = ? AND chat_id IN (SELECT chat_id FROM members WHERE user_id = ?)",
        (current_user, requested_user_id),
    )

    chat = cursor.fetchone()
    if chat:
        return {
            "status": "error",
            "message": "Chat already exists",
            "pfp": None,
            "status_code": 409,
        }

    # Create a new chat
    chat_id = str(uuid.uuid4())
    db.execute("INSERT INTO chats (chat_id, isGroup) VALUES (?, ?)", (chat_id, 0))
    db.execute(
        "INSERT INTO members (chat_id, user_id) VALUES (?, ?)", (chat_id, current_user)
    )
    db.execute(
        "INSERT INTO members (chat_id, user_id) VALUES (?, ?)",
        (chat_id, requested_user_id),
    )
    db.commit()
    return {
        "status": "success",
        "message": "Chat created successfully",
        "chat_id": chat_id,
        "pfp": requested_user["pfp"],
        "requested_id": requested_user_id,
        "status_code": 200,
    }
