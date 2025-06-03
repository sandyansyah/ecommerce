from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from app import db
from app.models import Product, CartItem

cart = Blueprint('cart', __name__)

@cart.route('/cart')
@login_required
def view_cart():
    """View shopping cart contents"""
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.quantity * item.product.price for item in cart_items)
    
    return render_template('cart/view.html', 
                          cart_items=cart_items,
                          total=total,
                          title='Your Shopping Cart')

@cart.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    """Add a product to the shopping cart"""
    product = Product.query.get_or_404(product_id)
    
    # Get quantity from form data, default to 1
    quantity = int(request.form.get('quantity', 1))
    
    # Check if product is in stock
    if product.stock < quantity:
        flash(f'Sorry, only {product.stock} items available', 'warning')
        return redirect(url_for('products.product_detail', product_id=product_id))
    
    # Check if product is already in cart
    cart_item = CartItem.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()
    
    if cart_item:
        # Update quantity if product is already in cart
        cart_item.quantity += quantity
        flash(f'Added {quantity} more {product.name} to your cart', 'success')
    else:
        # Add new item to cart
        cart_item = CartItem(
            user_id=current_user.id,
            product_id=product_id,
            quantity=quantity
        )
        db.session.add(cart_item)
        flash(f'Added {product.name} to your cart', 'success')
    
    db.session.commit()
    return redirect(url_for('cart.view_cart'))

@cart.route('/cart/update/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    """Update cart item quantity"""
    cart_item = CartItem.query.get_or_404(item_id)
    
    # Ensure the cart item belongs to the current user
    if cart_item.user_id != current_user.id:
        flash('You do not have permission to modify this cart item', 'danger')
        return redirect(url_for('cart.view_cart'))
    
    # Get new quantity from form data
    quantity = int(request.form.get('quantity', 1))
    
    # Check if product is in stock
    if cart_item.product.stock < quantity:
        flash(f'Sorry, only {cart_item.product.stock} items available', 'warning')
        return redirect(url_for('cart.view_cart'))
    
    if quantity > 0:
        cart_item.quantity = quantity
        flash('Cart updated successfully', 'success')
    else:
        # Remove item if quantity is 0 or negative
        db.session.delete(cart_item)
        flash('Item removed from cart', 'info')
    
    db.session.commit()
    return redirect(url_for('cart.view_cart'))

@cart.route('/cart/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    """Remove an item from the shopping cart"""
    cart_item = CartItem.query.get_or_404(item_id)
    
    # Ensure the cart item belongs to the current user
    if cart_item.user_id != current_user.id:
        flash('You do not have permission to modify this cart item', 'danger')
        return redirect(url_for('cart.view_cart'))
    
    db.session.delete(cart_item)
    db.session.commit()
    
    flash('Item removed from cart', 'info')
    return redirect(url_for('cart.view_cart'))

@cart.route('/cart/clear', methods=['POST'])
@login_required
def clear_cart():
    """Remove all items from the shopping cart"""
    CartItem.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    
    flash('Your cart has been cleared', 'info')
    return redirect(url_for('cart.view_cart'))

# AJAX endpoint for adding to cart
@cart.route('/api/cart/add/<int:product_id>', methods=['POST'])
@login_required
def api_add_to_cart(product_id):
    """AJAX endpoint for adding a product to the cart"""
    product = Product.query.get_or_404(product_id)
    
    # Get quantity from JSON data, default to 1
    data = request.get_json()
    quantity = int(data.get('quantity', 1)) if data else 1
    
    # Check if product is in stock
    if product.stock < quantity:
        return jsonify({
            'success': False,
            'message': f'Sorry, only {product.stock} items available'
        }), 400
    
    # Check if product is already in cart
    cart_item = CartItem.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()
    
    if cart_item:
        # Update quantity if product is already in cart
        cart_item.quantity += quantity
        message = f'Added {quantity} more {product.name} to your cart'
    else:
        # Add new item to cart
        cart_item = CartItem(
            user_id=current_user.id,
            product_id=product_id,
            quantity=quantity
        )
        db.session.add(cart_item)
        message = f'Added {product.name} to your cart'
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': message,
        'cart_count': current_user.get_cart_count(),
        'cart_total': current_user.get_cart_total()
    })