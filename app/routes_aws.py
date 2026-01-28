"""AWS Routes for FreshBakes - DynamoDB/SNS based routes."""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import os
from werkzeug.utils import secure_filename

# Import AWS model operations
from app.aws_models import (
    # Users
    get_user_by_email, create_user, verify_password, update_user,
    get_all_users, get_users_by_role,
    # Bakeries
    get_bakery_by_id, get_bakery_by_owner, get_bakery_by_slug,
    create_bakery, update_bakery, get_all_bakeries,
    get_approved_bakeries, get_featured_bakeries, approve_bakery,
    # Products
    get_product_by_id, get_products_by_bakery, create_product,
    update_product, delete_product, get_available_products,
    # Orders
    create_order as create_order_db, get_order_by_number,
    get_orders_by_customer, get_orders_by_bakery,
    update_order_status, get_all_orders,
    # Cart
    get_cart_items, add_to_cart, update_cart_item,
    remove_from_cart, clear_cart, get_cart_total,
    # Reviews
    create_review, get_reviews_by_bakery,
    # Categories
    get_categories_by_bakery, create_category,
    # Notifications
    notify_new_order, notify_order_status_change,
    notify_new_user_signup, notify_bakery_approved
)

# Create blueprints for AWS routes
aws_auth_bp = Blueprint('auth', __name__)
aws_main_bp = Blueprint('main', __name__)
aws_customer_bp = Blueprint('customer', __name__, url_prefix='/customer')
aws_baker_bp = Blueprint('baker', __name__, url_prefix='/baker')
aws_admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
aws_cart_bp = Blueprint('cart', __name__, url_prefix='/cart')
aws_orders_bp = Blueprint('orders', __name__, url_prefix='/orders')

# Configuration
UPLOAD_FOLDER = 'app/static/images'


def get_current_user():
    """Get current logged-in user from session."""
    if 'user_email' in session:
        return get_user_by_email(session['user_email'])
    return None


def login_required(f):
    """Decorator to require login."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            flash('Please log in to access this page.', 'info')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def baker_required(f):
    """Decorator to require baker role."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user or user.get('role') != 'baker':
            flash('Baker access required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin role."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user or user.get('role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


# ==================== AUTH ROUTES ====================

@aws_auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if 'user_email' in session:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').lower()
        password = request.form.get('password', '')
        
        user = verify_password(email, password)
        
        if user:
            if not user.get('is_active', True):
                flash('Your account has been deactivated.', 'danger')
                return render_template('auth/login.html')
            
            session['user_email'] = user['email']
            session['user_name'] = user.get('name', '')
            session['user_role'] = user.get('role', 'customer')
            
            flash(f"Welcome back, {user.get('name')}!", 'success')
            
            # Redirect based on role
            role = user.get('role', 'customer')
            if role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif role == 'baker':
                return redirect(url_for('baker.dashboard'))
            else:
                return redirect(url_for('main.index'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('auth/login.html')


@aws_auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Customer registration."""
    if 'user_email' in session:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').lower()
        password = request.form.get('password', '')
        name = request.form.get('name', '')
        phone = request.form.get('phone', '')
        
        # Check if user exists
        existing = get_user_by_email(email)
        if existing:
            flash('An account with this email already exists.', 'danger')
            return render_template('auth/register.html')
        
        # Create user
        user = create_user(email, password, name, phone, 'customer')
        
        if user:
            notify_new_user_signup(email, name, 'customer')
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Registration failed. Please try again.', 'danger')
    
    return render_template('auth/register.html')


@aws_auth_bp.route('/register/baker', methods=['GET', 'POST'])
def register_baker():
    """Baker registration."""
    if 'user_email' in session:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # User info
        email = request.form.get('email', '').lower()
        password = request.form.get('password', '')
        name = request.form.get('name', '')
        phone = request.form.get('phone', '')
        
        # Bakery info
        bakery_name = request.form.get('bakery_name', '')
        bakery_description = request.form.get('bakery_description', '')
        bakery_address = request.form.get('bakery_address', '')
        city = request.form.get('city', '')
        pincode = request.form.get('pincode', '')
        bakery_phone = request.form.get('bakery_phone', phone)
        
        # Check if user exists
        existing = get_user_by_email(email)
        if existing:
            flash('An account with this email already exists.', 'danger')
            return render_template('auth/register_baker.html')
        
        # Create user
        user = create_user(email, password, name, phone, 'baker')
        
        if user:
            # Create bakery
            bakery = create_bakery(
                owner_email=email,
                name=bakery_name,
                description=bakery_description,
                address=bakery_address,
                city=city,
                pincode=pincode,
                phone=bakery_phone,
                email=email
            )
            
            if bakery:
                notify_new_user_signup(email, name, 'baker')
                flash('Registration submitted! Your bakery is pending admin approval.', 'info')
                return redirect(url_for('auth.login'))
        
        flash('Registration failed. Please try again.', 'danger')
    
    return render_template('auth/register_baker.html')


@aws_auth_bp.route('/logout')
def logout():
    """User logout."""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


# ==================== MAIN ROUTES ====================

@aws_main_bp.route('/')
def index():
    """Home page."""
    featured_bakeries = get_featured_bakeries()
    approved_bakeries = get_approved_bakeries()
    
    return render_template('main/index.html', 
                         featured_bakeries=featured_bakeries,
                         bakeries=approved_bakeries[:8])


@aws_main_bp.route('/bakeries')
def bakeries():
    """List all bakeries."""
    all_bakeries = get_approved_bakeries()
    return render_template('main/bakeries.html', bakeries=all_bakeries)


@aws_main_bp.route('/bakery/<slug>')
def bakery_detail(slug):
    """Bakery detail page."""
    from app.aws_models.bakeries import get_bakery_by_slug
    
    bakery = get_bakery_by_slug(slug)
    if not bakery:
        flash('Bakery not found.', 'danger')
        return redirect(url_for('main.bakeries'))
    
    products = get_available_products(bakery['id'])
    categories = get_categories_by_bakery(bakery['id'])
    reviews = get_reviews_by_bakery(bakery['id'])
    
    return render_template('main/bakery_detail.html',
                         bakery=bakery,
                         products=products,
                         categories=categories,
                         reviews=reviews)


@aws_main_bp.route('/product/<product_id>')
def product_detail(product_id):
    """Product detail page."""
    product = get_product_by_id(product_id)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('main.index'))
    
    bakery = get_bakery_by_id(product['bakery_id'])
    
    return render_template('main/product_detail.html',
                         product=product,
                         bakery=bakery)


# ==================== CART ROUTES ====================

@aws_cart_bp.route('/')
@login_required
def view_cart():
    """View shopping cart."""
    user_email = session['user_email']
    cart_data = get_cart_total(user_email)
    
    # Enrich cart items with product details
    enriched_items = []
    for item in cart_data['items']:
        product = get_product_by_id(item['product_id'])
        if product:
            item['product'] = product
            enriched_items.append(item)
    
    return render_template('cart/view.html',
                         cart_items=enriched_items,
                         cart_total=cart_data['total'])


@aws_cart_bp.route('/add/<product_id>', methods=['POST'])
@login_required
def add_item(product_id):
    """Add item to cart."""
    user_email = session['user_email']
    quantity = int(request.form.get('quantity', 1))
    
    product = get_product_by_id(product_id)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get current price
    price = product.get('discount_price') or product.get('price', 0)
    
    add_to_cart(
        user_email=user_email,
        product_id=product_id,
        product_name=product.get('name', ''),
        quantity=quantity,
        unit_price=price
    )
    
    flash(f"Added {product.get('name')} to cart!", 'success')
    return redirect(request.referrer or url_for('main.index'))


@aws_cart_bp.route('/update/<product_id>', methods=['POST'])
@login_required
def update_item(product_id):
    """Update cart item quantity."""
    user_email = session['user_email']
    quantity = int(request.form.get('quantity', 1))
    
    if quantity <= 0:
        remove_from_cart(user_email, product_id)
        flash('Item removed from cart.', 'info')
    else:
        update_cart_item(user_email, product_id, quantity)
        flash('Cart updated.', 'success')
    
    return redirect(url_for('cart.view_cart'))


@aws_cart_bp.route('/remove/<product_id>')
@login_required
def remove_item(product_id):
    """Remove item from cart."""
    user_email = session['user_email']
    remove_from_cart(user_email, product_id)
    flash('Item removed from cart.', 'info')
    return redirect(url_for('cart.view_cart'))


# ==================== ORDER ROUTES ====================

@aws_orders_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """Checkout page."""
    user_email = session['user_email']
    user = get_user_by_email(user_email)
    cart_data = get_cart_total(user_email)
    
    if not cart_data['items']:
        flash('Your cart is empty.', 'info')
        return redirect(url_for('cart.view_cart'))
    
    if request.method == 'POST':
        # Get delivery address
        delivery_address = {
            'full_address': request.form.get('address', ''),
            'city': request.form.get('city', ''),
            'pincode': request.form.get('pincode', ''),
            'phone': request.form.get('phone', '')
        }
        
        payment_method = request.form.get('payment_method', 'cod')
        special_instructions = request.form.get('special_instructions', '')
        
        # Get bakery ID from first item
        first_item = cart_data['items'][0]
        product = get_product_by_id(first_item['product_id'])
        bakery_id = product.get('bakery_id') if product else ''
        bakery = get_bakery_by_id(bakery_id) if bakery_id else None
        
        # Prepare order items
        order_items = []
        for item in cart_data['items']:
            order_items.append({
                'product_id': item['product_id'],
                'product_name': item.get('product_name', ''),
                'quantity': item['quantity'],
                'unit_price': item['unit_price'],
                'subtotal': item['quantity'] * item['unit_price']
            })
        
        # Calculate totals
        delivery_fee = bakery.get('delivery_fee', 0) if bakery else 0
        
        # Create order
        order = create_order_db(
            customer_email=user_email,
            bakery_id=bakery_id,
            items=order_items,
            delivery_address=delivery_address,
            subtotal=cart_data['total'],
            delivery_fee=delivery_fee,
            discount=0,
            payment_method=payment_method,
            special_instructions=special_instructions
        )
        
        if order:
            # Clear cart
            clear_cart(user_email)
            
            # Send notification
            notify_new_order(
                order['order_number'],
                user_email,
                bakery.get('name', 'Unknown') if bakery else 'Unknown',
                order['total_amount'],
                len(order_items)
            )
            
            flash(f"Order {order['order_number']} placed successfully!", 'success')
            return redirect(url_for('orders.order_detail', order_number=order['order_number']))
        else:
            flash('Failed to place order. Please try again.', 'danger')
    
    return render_template('orders/checkout.html',
                         user=user,
                         cart_items=cart_data['items'],
                         cart_total=cart_data['total'])


@aws_orders_bp.route('/')
@login_required
def my_orders():
    """List user's orders."""
    user_email = session['user_email']
    orders = get_orders_by_customer(user_email)
    
    return render_template('orders/list.html', orders=orders)


@aws_orders_bp.route('/<order_number>')
@login_required
def order_detail(order_number):
    """Order detail page."""
    order = get_order_by_number(order_number)
    
    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('orders.my_orders'))
    
    # Verify user owns this order
    if order['customer_email'] != session['user_email'] and session.get('user_role') not in ['admin', 'baker']:
        flash('Access denied.', 'danger')
        return redirect(url_for('orders.my_orders'))
    
    bakery = get_bakery_by_id(order.get('bakery_id', ''))
    
    return render_template('orders/detail.html',
                         order=order,
                         bakery=bakery)


# ==================== BAKER ROUTES ====================

@aws_baker_bp.route('/dashboard')
@login_required
@baker_required
def dashboard():
    """Baker dashboard."""
    user_email = session['user_email']
    bakery = get_bakery_by_owner(user_email)
    
    if not bakery:
        flash('Bakery not found.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get recent orders
    orders = get_orders_by_bakery(bakery['id'])[:10]
    products = get_products_by_bakery(bakery['id'])
    
    return render_template('baker/dashboard.html',
                         bakery=bakery,
                         orders=orders,
                         products=products)


@aws_baker_bp.route('/products')
@login_required
@baker_required
def products():
    """Baker products list."""
    user_email = session['user_email']
    bakery = get_bakery_by_owner(user_email)
    
    if not bakery:
        return redirect(url_for('main.index'))
    
    all_products = get_products_by_bakery(bakery['id'])
    categories = get_categories_by_bakery(bakery['id'])
    
    return render_template('baker/products.html',
                         bakery=bakery,
                         products=all_products,
                         categories=categories)


@aws_baker_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
@baker_required
def add_product():
    """Add new product."""
    user_email = session['user_email']
    bakery = get_bakery_by_owner(user_email)
    
    if not bakery:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        name = request.form.get('name', '')
        description = request.form.get('description', '')
        price = float(request.form.get('price', 0))
        discount_price = request.form.get('discount_price')
        category_id = request.form.get('category_id', '')
        stock_quantity = int(request.form.get('stock_quantity', 0))
        is_vegetarian = request.form.get('is_vegetarian') == 'on'
        
        # Handle image upload
        image_url = 'default-product.png'
        if 'image' in request.files:
            image = request.files['image']
            if image.filename:
                filename = secure_filename(image.filename)
                image.save(os.path.join(UPLOAD_FOLDER, 'products', filename))
                image_url = filename
        
        product = create_product(
            bakery_id=bakery['id'],
            name=name,
            price=price,
            description=description,
            category_id=category_id,
            discount_price=float(discount_price) if discount_price else None,
            image_url=image_url,
            stock_quantity=stock_quantity,
            is_vegetarian=is_vegetarian
        )
        
        if product:
            flash(f"Product '{name}' added successfully!", 'success')
            return redirect(url_for('baker.products'))
        else:
            flash('Failed to add product.', 'danger')
    
    categories = get_categories_by_bakery(bakery['id'])
    return render_template('baker/add_product.html',
                         bakery=bakery,
                         categories=categories)


@aws_baker_bp.route('/orders')
@login_required
@baker_required
def orders():
    """Baker orders list."""
    user_email = session['user_email']
    bakery = get_bakery_by_owner(user_email)
    
    if not bakery:
        return redirect(url_for('main.index'))
    
    status_filter = request.args.get('status')
    all_orders = get_orders_by_bakery(bakery['id'], status=status_filter)
    
    return render_template('baker/orders.html',
                         bakery=bakery,
                         orders=all_orders)


@aws_baker_bp.route('/orders/<order_number>/update', methods=['POST'])
@login_required
@baker_required
def update_order(order_number):
    """Update order status."""
    new_status = request.form.get('status', '')
    
    order = get_order_by_number(order_number)
    if order:
        old_status = order.get('status', '')
        update_order_status(order_number, new_status)
        notify_order_status_change(order_number, order['customer_email'], old_status, new_status)
        flash(f"Order status updated to: {new_status}", 'success')
    else:
        flash('Order not found.', 'danger')
    
    return redirect(url_for('baker.orders'))


# ==================== ADMIN ROUTES ====================

@aws_admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard."""
    users = get_all_users()
    bakeries = get_all_bakeries()
    orders = get_all_orders()[:20]
    
    # Count stats
    pending_bakeries = [b for b in bakeries if not b.get('is_approved')]
    
    return render_template('admin/dashboard.html',
                         users=users,
                         bakeries=bakeries,
                         orders=orders,
                         pending_bakeries=pending_bakeries)


@aws_admin_bp.route('/bakeries')
@login_required
@admin_required
def bakeries_list():
    """Admin bakeries list."""
    bakeries = get_all_bakeries()
    return render_template('admin/bakeries.html', bakeries=bakeries)


@aws_admin_bp.route('/bakeries/<bakery_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_bakery_route(bakery_id):
    """Approve a bakery."""
    bakery = get_bakery_by_id(bakery_id)
    if bakery:
        approve_bakery(bakery_id)
        notify_bakery_approved(bakery.get('name', ''), bakery.get('owner_email', ''))
        flash(f"Bakery '{bakery.get('name')}' approved!", 'success')
    else:
        flash('Bakery not found.', 'danger')
    
    return redirect(url_for('admin.bakeries_list'))


@aws_admin_bp.route('/users')
@login_required
@admin_required
def users_list():
    """Admin users list."""
    users = get_all_users()
    return render_template('admin/users.html', users=users)


@aws_admin_bp.route('/orders')
@login_required
@admin_required
def orders_list():
    """Admin orders list."""
    orders = get_all_orders()
    return render_template('admin/orders.html', orders=orders)


def register_aws_blueprints(app):
    """Register all AWS blueprints with the app."""
    app.register_blueprint(aws_auth_bp)
    app.register_blueprint(aws_main_bp)
    app.register_blueprint(aws_customer_bp)
    app.register_blueprint(aws_baker_bp)
    app.register_blueprint(aws_admin_bp)
    app.register_blueprint(aws_cart_bp)
    app.register_blueprint(aws_orders_bp)
