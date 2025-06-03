from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import Product, Category
from app import db

products = Blueprint('products', __name__)

@products.route('/products')
def list_products():
    """List all products or filter by category"""
    page = request.args.get('page', 1, type=int)
    per_page = 12  # Number of products per page
    
    # Get category filter if provided
    category_id = request.args.get('category', type=int)
    sort_by = request.args.get('sort', 'name')  # Default sort by name
    
    # Base query
    query = Product.query
    
    # Apply category filter if provided
    if category_id:
        query = query.filter_by(category_id=category_id)
        category = Category.query.get_or_404(category_id)
        title = f'{category.name} Products'
    else:
        title = 'All Products'
    
    # Apply sorting
    if sort_by == 'price_low':
        query = query.order_by(Product.price)
    elif sort_by == 'price_high':
        query = query.order_by(Product.price.desc())
    elif sort_by == 'newest':
        query = query.order_by(Product.date_added.desc())
    else:  # Default sort by name
        query = query.order_by(Product.name)
    
    # Paginate results
    products = query.paginate(page=page, per_page=per_page)
    
    # Get all categories for the sidebar
    categories = Category.query.all()
    
    return render_template('products/list.html', 
                          products=products,
                          categories=categories,
                          current_category=category_id,
                          sort_by=sort_by,
                          title=title)

@products.route('/products/<int:product_id>')
def product_detail(product_id):
    """Display product details"""
    product = Product.query.get_or_404(product_id)
    
    # Get related products (same category)
    related_products = Product.query.filter(
        (Product.category_id == product.category_id) &
        (Product.id != product.id)
    ).limit(4).all()
    
    return render_template('products/detail.html', 
                          product=product,
                          related_products=related_products,
                          title=product.name)

@products.route('/category/<int:category_id>')
def category(category_id):
    """Redirect to products list with category filter"""
    return redirect(url_for('products.list_products', category=category_id))