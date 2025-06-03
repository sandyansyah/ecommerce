from datetime import datetime
import enum
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

# Enum untuk role pengguna
class UserRole(enum.Enum):
    CUSTOMER = "customer"
    SELLER = "seller"
    ADMIN = "admin"

# Association table for cart items
class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    
    product = db.relationship('Product', backref='cart_items')

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    address = db.Column(db.String(200))
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    zip_code = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    date_registered = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.Enum(UserRole), default=UserRole.CUSTOMER)
    is_active = db.Column(db.Boolean, default=True)
    
    # Tambahkan relasi ke toko jika pengguna adalah seller
    store = db.relationship('Store', backref='owner', uselist=False, lazy=True)
    
    orders = db.relationship('Order', backref='customer', lazy=True)
    cart_items = db.relationship('CartItem', backref='user', lazy=True, 
                                cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_cart_count(self):
        return sum(item.quantity for item in self.cart_items)
    
    def get_cart_total(self):
        return sum(item.quantity * item.product.price for item in self.cart_items)
    
    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN
    
    @property
    def is_seller(self):
        return self.role == UserRole.SELLER

# Product Category model
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    
    products = db.relationship('Product', backref='category', lazy=True)

# Model untuk toko (untuk seller)
class Store(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    logo = db.Column(db.String(100), default='default_store.jpg')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    products = db.relationship('Product', backref='store', lazy=True)

# Product model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    image = db.Column(db.String(100), default='default_product.jpg')
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'), nullable=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    is_featured = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'image': self.image
        }

# Order model
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, paid, shipped, delivered
    payment_method = db.Column(db.String(20))
    shipping_address = db.Column(db.String(200))
    shipping_city = db.Column(db.String(50))
    shipping_state = db.Column(db.String(50))
    shipping_zip = db.Column(db.String(20))
    shipping_phone = db.Column(db.String(20))
    
    items = db.relationship('OrderItem', backref='order', lazy=True, 
                           cascade='all, delete-orphan')

# Order Item model
class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    
    product = db.relationship('Product')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def initialize_db():
    """Initialize the database with some sample data if empty"""
    # Check if database is empty
    if Category.query.first() is None:
        # Create categories
        categories = [
            Category(name='Electronics', description='Electronic gadgets and devices'),
            Category(name='Clothing', description='Fashion items and accessories'),
            Category(name='Home & Kitchen', description='Home decoration and kitchen appliances'),
            Category(name='Books', description='Books of various genres')
        ]
        db.session.add_all(categories)
        db.session.commit()
        
        # Create admin user
        admin = User(
            username='admin',
            email='admin@example.com',
            role=UserRole.ADMIN,
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Create sample seller
        seller = User(
            username='seller',
            email='seller@example.com',
            role=UserRole.SELLER,
            first_name='John',
            last_name='Seller',
            is_active=True
        )
        seller.set_password('seller123')
        db.session.add(seller)
        db.session.flush()  # To get seller ID
        
        # Create store for seller
        store = Store(
            name='Tech Shop',
            description='Quality technology products',
            user_id=seller.id
        )
        db.session.add(store)
        db.session.flush()  # To get store ID
        
        # Create sample products
        products = [
            Product(
                name='Smartphone X', 
                description='Latest smartphone with amazing features',
                price=699.99,
                stock=50,
                image='smartphone.jpg',
                category_id=1,
                store_id=store.id,
                is_featured=True
            ),
            Product(
                name='Laptop Pro', 
                description='Powerful laptop for professionals',
                price=1299.99,
                stock=30,
                image='laptop.jpg',
                category_id=1,
                store_id=store.id,
                is_featured=True
            ),
            Product(
                name='Designer T-shirt', 
                description='Comfortable cotton t-shirt with stylish design',
                price=29.99,
                stock=100,
                image='tshirt.jpg',
                category_id=2,
                store_id=store.id
            ),
            Product(
                name='Smart Watch', 
                description='Track your fitness and stay connected',
                price=199.99,
                stock=45,
                image='smartwatch.jpg',
                category_id=1,
                store_id=store.id,
                is_featured=True
            ),
            Product(
                name='Coffee Maker', 
                description='Brew perfect coffee every morning',
                price=89.99,
                stock=25,
                image='coffeemaker.jpg',
                category_id=3,
                store_id=store.id
            ),
            Product(
                name='Best-selling Novel', 
                description='The latest best-selling fiction novel',
                price=19.99,
                stock=200,
                image='book.jpg',
                category_id=4,
                store_id=store.id
            )
        ]
        db.session.add_all(products)
        
        db.session.commit()