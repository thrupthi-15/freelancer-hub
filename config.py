import os
class Config:
    SECRET_KEY = 'freelancers_hub_secret_2024'
    MYSQL_HOST     = 'localhost'
    MYSQL_USER     = 'root'
    MYSQL_PASSWORD = 'root'        # <-- Set your MySQL password here
    MYSQL_DB       = 'freelancers'
    MYSQL_PORT     = 3307
    BASE_DIR          = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER     = os.path.join(BASE_DIR, 'static', 'uploads')
    PROFILE_FOLDER    = os.path.join(BASE_DIR, 'static', 'uploads', 'profiles')
    ATTACHMENT_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'attachments')
    VIDEO_FOLDER      = os.path.join(BASE_DIR, 'static', 'uploads', 'videos')
    ALLOWED_IMAGE_EXT = {'png','jpg','jpeg','gif'}
    ALLOWED_PDF_EXT   = {'pdf'}
    ALLOWED_VIDEO_EXT = {'mp4','avi','mov','mkv','webm'}
    MAX_CONTENT_LENGTH = 200 * 1024 * 1024
