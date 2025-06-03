import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_class=Config):
    # Create and configure the app
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions with the app
    db.init_app(app)
    login_manager.init_app(app)
    
    # Set login view for the login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Make sure instance folder exists
    os.makedirs(os.path.dirname(app.instance_path), exist_ok=True)
    
    # Register blueprints
    from app.routes.main import main
    from app.routes.auth import auth
    from app.routes.products import products
    from app.routes.cart import cart
    from app.routes.orders import orders
    from app.routes.admin import admin
    from app.routes.seller import seller  # Import seller blueprint
    
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(products)
    app.register_blueprint(cart)
    app.register_blueprint(orders)
    app.register_blueprint(admin)
    app.register_blueprint(seller)  # Register seller blueprint
    
    # Create database tables
    with app.app_context():
        db.create_all()
        from app.models import initialize_db
        initialize_db()
    
    return app