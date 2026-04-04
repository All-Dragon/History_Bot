import hashlib

import bcrypt


def _prepare(password: str) -> bytes:
    return hashlib.sha256(password.encode("utf-8")).hexdigest().encode("ascii")


def hash_password(password: str) -> str:
    prepared_password = _prepare(password)
    hashed_password = bcrypt.hashpw(prepared_password, bcrypt.gensalt())
    return hashed_password.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    prepared_password = _prepare(password)
    return bcrypt.checkpw(prepared_password, hashed.encode("utf-8"))
