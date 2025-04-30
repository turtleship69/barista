import hashlib
import time

def gravatar(email: str) -> str:
    """
    Generate a Gravatar URL for the given email address.

    Args:
        email (str): The email address to generate the Gravatar for.

    Returns:
        str: The URL of the Gravatar image.
    """
    # Convert the email to a hash using MD5
    email_hash = hashlib.md5(email.lower().encode('utf-8')).hexdigest()

    # Build the Gravatar URL
    url = f'https://www.gravatar.com/avatar/{email_hash}'

    return url



def utc_now():
    return int(time.time())