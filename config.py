import os
import sqlite3
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "ecommerce.db")

# Pastikan database file exists
conn = sqlite3.connect(db_path)
conn.close()

class Config:
    # Secret key for session management and CSRF protection
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # Gunakan path absolut untuk database di root folder
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{db_path}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload folder for product images
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    
    # Maximum file size for uploads (5MB)
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    
    # Session lifetime
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Payment settings (replace with actual keys in production)
    PAYMENT_API_KEY = os.environ.get('PAYMENT_API_KEY') or 'dummy-payment-api-key'