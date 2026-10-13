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

    PERSONAL_INFORMATION_SAVED_SUCCESSFULLY = "Personal information Saved Successfully!"
    PERSONAL_INFORMATION_UPDATED_SUCCESSFULLY = "Personal information Updated Successfully!"
    PROFESSIONAL_SUMMARY_SAVED_SUCCESSFULLY = "Professional Summary Saved Successfully!"
    PROFESSIONAL_SUMMARY_UPDATED_SUCCESSFULLY = "Professional Summary Updated Successfully!"

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

    # Resume Service
    PERSONAL_INFO_ALREADY_EXISTS = "personal information already exist!"
    PERSONAL_INFO__NOT_FOUND = "personal information not found!"
    PROFESSIONAL_SUMMARY_ALREADY_EXIST = "professional summary already exist!"
    PROFESSIONAL_SUMMARY_NOT_FOUND = "professional summary not found!"

class LoggerMessage:
    ExpiredSignatureError_Logtext = "user_id :: {user_id} & error :: {e}"
