"""
Static API response and logger messages.
"""


class SuccessMessage:
    SERVER_HEALTHY = "Server is Healthy!"
    RESPONSE_FETCHED_SUCCESSFULLY = "Response Fetched Successfully"
    USER_REGISTERED_SUCCESSFULLY = "User Registered Successfully!"
    USER_VERIFICATION_EMAIL_SEND = "User Verification Email Sent"
    USER_OTP_VERIFIED_SUCCESSFULLY = "User OTP Verified Successfully"
    USER_LOGIN_SUCCESSFULLY = "User Login Successfully!"
    USER_CHANGE_PASSWORD_SUCCESSFULLY = "Password Changed Successfully!"
    USER_SESSION_REFRESHED_SUCCESSFULLY = "Session Refreshed Successfully!"

class ErrorMessage:
    TOKEN_EXPIRE = "Token Expired!"
    INVALID_TOKEN = "Token Invalid!"
    INTERNAL_SERVER_ERROR = "Internal Server Error!"
    UNAUTHORIZED_ACCESS = "You are not Authorized to Access!"
    INVALID_CREDENTIALS = "Invalid Credentials!"
    USER_ALREADY_EXIST = "User Already Exists!"
    ROLE_NOT_FOUND = "Role Not Found!"
    USER_ALREADY_VERIFIED = "User Already Verified"
    OTP_EXPIRED = "OTP Expired!"
    OTP_INVALID = "OTP Invalid!"
    USER_INACTIVE = "User Inactive!"
    USER_NOT_FOUND = "User not found"
    WRONG_OLD_PASSWORD = "Wrong Old Password!"
    SESSION_EXPIRED = "Session Expired"
    USER_SESSION_NOT_FOUND = "User Session Not Found"


class LoggerMessage:
    ExpiredSignatureError_Logtext = "user_id :: {user_id} & error :: {e}"
