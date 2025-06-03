from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from app import db
from app.models import Product, CartItem, Order, OrderItem
import json

orders = Blueprint('orders', __name__)

@orders.route('/checkout', methods=['GET'])
@login_required
def checkout():
    """Checkout page displaying cart summary and payment options"""
    # Get cart items
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    
    if not cart_items:
        flash('Your cart is empty', 'info')
        return redirect(url_for('cart.view_cart'))
    
    # Calculate total
    subtotal = sum(item.quantity * item.product.price for item in cart_items)
    shipping = 10.00  # Fixed shipping cost
    tax = subtotal * 0.08  # 8% tax
    total = subtotal + shipping + tax
    
    return render_template('cart/checkout.html',
                          cart_items=cart_items,
                          subtotal=subtotal,
                          shipping=shipping,
                          tax=tax,
                          total=total,
                          user=current_user,
                          title='Checkout')

@orders.route('/place-order', methods=['POST'])
@login_required
def place_order():
    """Process the order submission"""
    # Get cart items
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    
    if not cart_items:
        flash('Your cart is empty', 'info')
        return redirect(url_for('cart.view_cart'))
    
    # Calculate total
    subtotal = sum(item.quantity * item.product.price for item in cart_items)
    shipping = 10.00
    tax = subtotal * 0.08
    total = subtotal + shipping + tax
    
    # Get form data
    payment_method = request.form.get('payment_method')
    
    # Use user's profile address or the one provided in the form
    use_profile_address = request.form.get('use_profile_address') == 'on'
    
    if use_profile_address:
        shipping_address = current_user.address
        shipping_city = current_user.city
        shipping_state = current_user.state
        shipping_zip = current_user.zip_code
        shipping_phone = current_user.phone
    else:
        shipping_address = request.form.get('shipping_address')
        shipping_city = request.form.get('shipping_city')
        shipping_state = request.form.get('shipping_state')
        shipping_zip = request.form.get('shipping_zip')
        shipping_phone = request.form.get('shipping_phone')
    
    # Create order
    order = Order(
        user_id=current_user.id,
        total_price=total,
        payment_method=payment_method,
        shipping_address=shipping_address,
        shipping_city=shipping_city,
        shipping_state=shipping_state,
        shipping_zip=shipping_zip,
        shipping_phone=shipping_phone,
        status='pending'  # Initial status
    )
    
    db.session.add(order)
    db.session.flush()  # Get order ID without committing
    
    # Create order items
    for cart_item in cart_items:
        product = cart_item.product
        
        # Check if product is still in stock
        if product.stock < cart_item.quantity:
            flash(f'Sorry, {product.name} is now out of stock or has insufficient quantity', 'danger')
            return redirect(url_for('cart.view_cart'))
        
        # Create order item
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            quantity=cart_item.quantity,
            price=product.price
        )
        db.session.add(order_item)
        
        # Update product stock
        product.stock -= cart_item.quantity
    
    # Process payment (simplified for this example)
    # In a real application, you would integrate with a payment gateway here
    if payment_method == 'credit_card':
        # Simulate credit card payment processing
        # In a real app, you would use a payment gateway API
        order.status = 'paid'
    elif payment_method == 'paypal':
        # Simulate PayPal payment processing
        order.status = 'paid'
    else:  # Cash on delivery
        order.status = 'pending'
    
    # Clear the cart
    CartItem.query.filter_by(user_id=current_user.id).delete()
    
    # Commit all changes
    db.session.commit()
    
    flash('Your order has been placed successfully!', 'success')
    return redirect(url_for('orders.order_confirmation', order_id=order.id))

@orders.route('/order-confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    """Order confirmation page"""
    order = Order.query.get_or_404(order_id)
    
    # Ensure the order belongs to the current user
    if order.user_id != current_user.id:
        flash('You do not have permission to view this order', 'danger')
        return redirect(url_for('main.home'))
    
    return render_template('orders/confirm.html',
                          order=order,
                          title='Order Confirmation')

@orders.route('/orders')
@login_required
def order_history():
    """Display user's order history"""
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.order_date.desc()).all()
    
    return render_template('orders/history.html',
                          orders=orders,
                          title='Order History')

@orders.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    """Display details for a specific order"""
    order = Order.query.get_or_404(order_id)
    
    # Ensure the order belongs to the current user
    if order.user_id != current_user.id:
        flash('You do not have permission to view this order', 'danger')
        return redirect(url_for('orders.order_history'))
    
    return render_template('orders/detail.html',
                          order=order,
                          title=f'Order #{order.id}')