from app.core.config import settings

# JWT Constants
JWT_ACCESS_TOKEN_EXPIRY_TIME = settings.JWT_ACCESS_TOKEN_EXPIRY
JWT_REFRESH_TOKEN_EXPIRY_TIME = settings.JWT_REFRESH_TOKEN_EXPIRY

# Role Constants
class Roles:
    ADMIN = "admin"
    EMPLOYEE = "employee"
    USER = "user"

# RESUME FILE SIZE IN MB
RESUME_FILE_SIZE = 10