from flask import Blueprint, render_template, request
from app.models import Product, Category

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/home')
def home():
    """Home page route showing featured products"""
    featured_products = Product.query.filter_by(is_featured=True).limit(4).all()
    categories = Category.query.all()
    return render_template('home.html', 
                          featured_products=featured_products,
                          categories=categories,
                          title='Welcome to ShopEasy')

@main.route('/about')
def about():
    """About page route"""
    return render_template('about.html', title='About Us')

@main.route('/contact')
def contact():
    """Contact page route"""
    return render_template('contact.html', title='Contact Us')

@main.route('/search')
def search():
    """Search products functionality"""
    query = request.args.get('query', '')
    if not query:
        return render_template('products/list.html', 
                              products=[],
                              title='Search Results',
                              search_query='')
    
    # Search in product name and description
    products = Product.query.filter(
        (Product.name.like(f'%{query}%')) | 
        (Product.description.like(f'%{query}%'))
    ).all()
    
    return render_template('products/list.html', 
                          products=products,
                          title='Search Results',
                          search_query=query)