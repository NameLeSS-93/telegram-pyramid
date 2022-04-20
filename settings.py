import os


def load_settings():
    return {"TOKEN_API": os.environ.get("TOKEN_API")}
