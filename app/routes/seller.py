from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from app import db
from app.models import User, UserRole, Product, Category, Store
from app.utils import save_picture
from functools import wraps

seller = Blueprint('seller', __name__)

# Decorator untuk membatasi akses ke halaman seller
def seller_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != UserRole.SELLER:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@seller.route('/seller')
@login_required
@seller_required
def dashboard():
    """Seller dashboard showing overview stats"""
    # Get seller's store
    store = current_user.store
    
    if not store:
        # Create a store for seller if they don't have one
        store = Store(
            name=f"{current_user.first_name or current_user.username}'s Store",
            description="Welcome to my store!",
            user_id=current_user.id
        )
        db.session.add(store)
        db.session.commit()
    
    # Get counts for overview
    product_count = Product.query.filter_by(store_id=store.id).count()
    
    # Get seller's products
    recent_products = Product.query.filter_by(store_id=store.id).order_by(Product.date_added.desc()).limit(5).all()
    
    # Get featured products
    featured_products = Product.query.filter_by(store_id=store.id, is_featured=True).all()
    
    return render_template('seller/dashboard.html',
                          title='Seller Dashboard',
                          store=store,
                          product_count=product_count,
                          recent_products=recent_products,
                          featured_products=featured_products)

@seller.route('/seller/products')
@login_required
@seller_required
def product_list():
    """List all products for the seller"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get query parameters for filtering
    category_id = request.args.get('category', type=int)
    search = request.args.get('search')
    
    # Base query - only show products from seller's store
    query = Product.query.filter_by(store_id=current_user.store.id)
    
    # Apply filters
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if search:
        query = query.filter(
            (Product.name.ilike(f'%{search}%')) |
            (Product.description.ilike(f'%{search}%'))
        )
    
    # Paginate results
    products = query.order_by(Product.date_added.desc()).paginate(page=page, per_page=per_page)
    
    # Get all categories for the filter dropdown
    categories = Category.query.all()
    
    return render_template('seller/product_list.html',
                          title='My Products',
                          products=products,
                          categories=categories,
                          category_filter=category_id,
                          search=search)

@seller.route('/seller/products/add', methods=['GET', 'POST'])
@login_required
@seller_required
def product_add():
    """Add a new product"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        stock = int(request.form.get('stock'))
        category_id = int(request.form.get('category_id'))
        is_featured = 'is_featured' in request.form
        
        # Handle image upload
        image = 'default_product.jpg'
        if 'image' in request.files and request.files['image'].filename:
            try:
                image = save_picture(request.files['image'], 'product_pics')
            except Exception as e:
                flash(f'Error uploading image: {str(e)}', 'danger')
        
        # Create new product
        product = Product(
            name=name,
            description=description,
            price=price,
            stock=stock,
            image=image,
            category_id=category_id,
            store_id=current_user.store.id,
            is_featured=is_featured
        )
        
        db.session.add(product)
        db.session.commit()
        
        flash(f'Product {name} has been added!', 'success')
        return redirect(url_for('seller.product_list'))
    
    # Get all categories for the form
    categories = Category.query.all()
    
    return render_template('seller/product_add.html',
                          title='Add Product',
                          categories=categories)

@seller.route('/seller/products/<int:product_id>', methods=['GET', 'POST'])
@login_required
@seller_required
def product_edit(product_id):
    """Edit product details"""
    product = Product.query.get_or_404(product_id)
    
    # Ensure the product belongs to the seller's store
    if product.store_id != current_user.store.id:
        abort(403)
    
    if request.method == 'POST':
        # Update product details
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.price = float(request.form.get('price'))
        product.stock = int(request.form.get('stock'))
        product.category_id = int(request.form.get('category_id'))
        product.is_featured = 'is_featured' in request.form
        
        # Handle image upload
        if 'image' in request.files and request.files['image'].filename:
            try:
                picture_file = save_picture(request.files['image'], 'product_pics')
                product.image = picture_file
            except Exception as e:
                flash(f'Error uploading image: {str(e)}', 'danger')
        
        db.session.commit()
        flash(f'Product {product.name} has been updated successfully!', 'success')
        return redirect(url_for('seller.product_list'))
    
    # Get all categories for the form
    categories = Category.query.all()
    
    return render_template('seller/product_edit.html',
                          title='Edit Product',
                          product=product,
                          categories=categories)

@seller.route('/seller/products/<int:product_id>/delete', methods=['POST'])
@login_required
@seller_required
def product_delete(product_id):
    """Delete a product"""
    product = Product.query.get_or_404(product_id)
    
    # Ensure the product belongs to the seller's store
    if product.store_id != current_user.store.id:
        abort(403)
    
    db.session.delete(product)
    db.session.commit()
    
    flash(f'Product {product.name} has been deleted!', 'success')
    return redirect(url_for('seller.product_list'))

@seller.route('/seller/store', methods=['GET', 'POST'])
@login_required
@seller_required
def store_edit():
    """Edit store details"""
    store = current_user.store
    
    if request.method == 'POST':
        # Update store details
        store.name = request.form.get('name')
        store.description = request.form.get('description')
        
        # Handle logo upload
        if 'logo' in request.files and request.files['logo'].filename:
            try:
                logo_file = save_picture(request.files['logo'], 'store_logos')
                store.logo = logo_file
            except Exception as e:
                flash(f'Error uploading logo: {str(e)}', 'danger')
        
        db.session.commit()
        flash('Your store information has been updated!', 'success')
        return redirect(url_for('seller.store_edit'))
    
    return render_template('seller/store_edit.html',
                          title='Edit Store',
                          store=store)