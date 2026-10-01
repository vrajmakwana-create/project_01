from enum import Enum


class LoginType(str, Enum):
    EMAIL = "email"
    GOOGLE = "google"
    GITHUB = "github"
    FACEBOOK = "facebook"
