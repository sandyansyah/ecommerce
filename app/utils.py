import os
import secrets
from PIL import Image
from flask import current_app
import re

def save_picture(form_picture, folder='product_pics'):
    """Save uploaded picture with a random name and resize it"""
    # Generate random filename to avoid collisions
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    
    # Determine the folder path
    folder_path = os.path.join(current_app.root_path, 'static', folder)
    os.makedirs(folder_path, exist_ok=True)
    
    # Create full path
    picture_path = os.path.join(folder_path, picture_fn)
    
    # Resize and save the image
    output_size = (800, 800)  # Max dimensions while preserving aspect ratio
    i = Image.open(form_picture)
    
    # Preserve aspect ratio
    i.thumbnail(output_size)
    
    # Save the image
    i.save(picture_path)
    
    return os.path.join(folder, picture_fn)

def validate_email(email):
    """Simple email validation"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))

def validate_password(password):
    """Simple password validation - at least 8 characters"""
    return len(password) >= 8

def format_price(price):
    """Format price with 2 decimal places and currency symbol"""
    return f"${price:.2f}"

def generate_order_number():
    """Generate a unique order number"""
    return f"ORD-{secrets.token_hex(6).upper()}"