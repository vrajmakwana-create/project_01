from pwdlib import PasswordHash

password_hasher = PasswordHash.recommended()


def password_hash(plain_text: str) -> str:
    """Take plain text password and return hashed text."""
    return password_hasher.hash(plain_text)


def verify_password(plain_text: str, hash_text: str) -> bool:
    """Verify plain text password against hash."""
    return password_hasher.verify(plain_text, hash_text)
