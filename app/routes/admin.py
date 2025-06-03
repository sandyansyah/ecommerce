from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from app import db
from app.models import User, UserRole, Product, Category, Order, Store
from app.utils import save_picture
from functools import wraps

admin = Blueprint('admin', __name__)

# Decorator untuk membatasi akses ke halaman admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != UserRole.ADMIN:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/admin')
@login_required
@admin_required
def dashboard():
    """Admin dashboard showing overview stats"""
    # Get counts for overview
    user_count = User.query.count()
    product_count = Product.query.count()
    order_count = Order.query.count()
    
    # Get recent orders
    recent_orders = Order.query.order_by(Order.order_date.desc()).limit(5).all()
    
    # Get sales data
    total_sales = db.session.query(db.func.sum(Order.total_price)).scalar() or 0
    
    # Get user role distribution
    customer_count = User.query.filter_by(role=UserRole.CUSTOMER).count()
    seller_count = User.query.filter_by(role=UserRole.SELLER).count()
    admin_count = User.query.filter_by(role=UserRole.ADMIN).count()
    
    return render_template('admin/dashboard.html',
                          title='Admin Dashboard',
                          user_count=user_count,
                          product_count=product_count,
                          order_count=order_count,
                          recent_orders=recent_orders,
                          total_sales=total_sales,
                          customer_count=customer_count,
                          seller_count=seller_count,
                          admin_count=admin_count)

@admin.route('/admin/users')
@login_required
@admin_required
def user_list():
    """List all users"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get query parameters for filtering
    role = request.args.get('role')
    search = request.args.get('search')
    
    # Base query
    query = User.query
    
    # Apply filters
    if role:
        query = query.filter_by(role=UserRole(role))
    
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%')) |
            (User.first_name.ilike(f'%{search}%')) |
            (User.last_name.ilike(f'%{search}%'))
        )
    
    # Paginate results
    users = query.order_by(User.date_registered.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('admin/user_list.html',
                          title='User Management',
                          users=users,
                          role_filter=role,
                          search=search)

@admin.route('/admin/users/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def user_edit(user_id):
    """Edit user details including role"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        # Update user details
        user.username = request.form.get('username', user.username)
        user.email = request.form.get('email', user.email)
        user.first_name = request.form.get('first_name', user.first_name)
        user.last_name = request.form.get('last_name', user.last_name)
        user.is_active = 'is_active' in request.form
        
        # Handle role change
        new_role = UserRole(request.form.get('role'))
        old_role = user.role
        
        if new_role != old_role:
            user.role = new_role
            
            # If user becomes a seller, create a store
            if new_role == UserRole.SELLER and old_role != UserRole.SELLER and not user.store:
                store_name = f"{user.first_name or user.username}'s Store"
                store = Store(
                    name=store_name,
                    description="Welcome to my store!",
                    user_id=user.id
                )
                db.session.add(store)
        
        # Handle password change if provided
        new_password = request.form.get('new_password')
        if new_password:
            user.set_password(new_password)
        
        db.session.commit()
        flash(f'User {user.username} has been updated successfully!', 'success')
        return redirect(url_for('admin.user_list'))
    
    return render_template('admin/user_edit.html',
                          title='Edit User',
                          user=user)

@admin.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def user_delete(user_id):
    """Delete a user"""
    user = User.query.get_or_404(user_id)
    
    # Prevent self-deletion
    if user == current_user:
        flash('You cannot delete your own account!', 'danger')
        return redirect(url_for('admin.user_list'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {user.username} has been deleted!', 'success')
    return redirect(url_for('admin.user_list'))

@admin.route('/admin/products')
@login_required
@admin_required
def product_list():
    """List all products"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get query parameters for filtering
    category_id = request.args.get('category', type=int)
    search = request.args.get('search')
    
    # Base query
    query = Product.query
    
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
    
    return render_template('admin/product_list.html',
                          title='Product Management',
                          products=products,
                          categories=categories,
                          category_filter=category_id,
                          search=search)

@admin.route('/admin/products/<int:product_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def product_edit(product_id):
    """Edit product details"""
    product = Product.query.get_or_404(product_id)
    
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
        return redirect(url_for('admin.product_list'))
    
    # Get all categories for the form
    categories = Category.query.all()
    
    return render_template('admin/product_edit.html',
                          title='Edit Product',
                          product=product,
                          categories=categories)

@admin.route('/admin/products/<int:product_id>/delete', methods=['POST'])
@login_required
@admin_required
def product_delete(product_id):
    """Delete a product"""
    product = Product.query.get_or_404(product_id)
    
    db.session.delete(product)
    db.session.commit()
    
    flash(f'Product {product.name} has been deleted!', 'success')
    return redirect(url_for('admin.product_list'))

@admin.route('/admin/orders')
@login_required
@admin_required
def order_list():
    """List all orders"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get query parameters for filtering
    status = request.args.get('status')
    search = request.args.get('search')
    
    # Base query
    query = Order.query
    
    # Apply filters
    if status:
        query = query.filter_by(status=status)
    
    if search:
        query = query.join(User).filter(
            (User.username.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%'))
        )
    
    # Paginate results
    orders = query.order_by(Order.order_date.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('admin/order_list.html',
                          title='Order Management',
                          orders=orders,
                          status_filter=status,
                          search=search)

@admin.route('/admin/orders/<int:order_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def order_detail(order_id):
    """View and update order status"""
    order = Order.query.get_or_404(order_id)
    
    if request.method == 'POST':
        # Update order status
        order.status = request.form.get('status')
        db.session.commit()
        flash(f'Order #{order.id} status has been updated to {order.status}!', 'success')
        return redirect(url_for('admin.order_list'))
    
    return render_template('admin/order_detail.html',
                          title=f'Order #{order.id}',
                          order=order)

@admin.route('/admin/categories')
@login_required
@admin_required
def category_list():
    """List all categories"""
    categories = Category.query.all()
    
    return render_template('admin/category_list.html',
                          title='Category Management',
                          categories=categories)

@admin.route('/admin/categories/add', methods=['GET', 'POST'])
@login_required
@admin_required
def category_add():
    """Add a new category"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        # Check if category with the same name already exists
        if Category.query.filter_by(name=name).first():
            flash(f'Category {name} already exists!', 'danger')
            return redirect(url_for('admin.category_add'))
        
        category = Category(
            name=name,
            description=description
        )
        
        db.session.add(category)
        db.session.commit()
        
        flash(f'Category {name} has been added!', 'success')
        return redirect(url_for('admin.category_list'))
    
    return render_template('admin/category_add.html',
                          title='Add Category')

@admin.route('/admin/categories/<int:category_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def category_edit(category_id):
    """Edit category details"""
    category = Category.query.get_or_404(category_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        
        # Check if category with the same name already exists
        existing_category = Category.query.filter_by(name=name).first()
        if existing_category and existing_category.id != category.id:
            flash(f'Category {name} already exists!', 'danger')
            return redirect(url_for('admin.category_edit', category_id=category.id))
        
        category.name = name
        category.description = request.form.get('description')
        
        db.session.commit()
        flash(f'Category {category.name} has been updated!', 'success')
        return redirect(url_for('admin.category_list'))
    
    return render_template('admin/category_edit.html',
                          title='Edit Category',
                          category=category)

@admin.route('/admin/categories/<int:category_id>/delete', methods=['POST'])
@login_required
@admin_required
def category_delete(category_id):
    """Delete a category"""
    category = Category.query.get_or_404(category_id)
    
    # Check if category has products
    if category.products:
        flash(f'Cannot delete category {category.name} because it has products!', 'danger')
        return redirect(url_for('admin.category_list'))
    
    db.session.delete(category)
    db.session.commit()
    
    flash(f'Category {category.name} has been deleted!', 'success')
    return redirect(url_for('admin.category_list'))