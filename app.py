from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json
import logging
from io import BytesIO
import csv
from io import StringIO
from sqlalchemy import inspect, text
from logging.handlers import RotatingFileHandler

# Load environment variables
# In production, these will come from system environment variables
# In development, load from .env file if it exists
if os.path.exists('.env'):
    load_dotenv('.env')
elif os.path.exists('development.env'):
    load_dotenv('development.env')
else:
    load_dotenv()  # Try system environment variables

# Configure logging
def setup_logging():
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Console logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format
    )
    
    # File logging for production
    if os.getenv('FLASK_ENV') == 'production':
        try:
            if not os.path.exists('logs'):
                os.makedirs('logs')
            file_handler = RotatingFileHandler('logs/app.log', maxBytes=1024*1024, backupCount=10)
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(logging.Formatter(log_format))
            logging.getLogger().addHandler(file_handler)
        except Exception as e:
            print(f"Could not setup file logging: {e}")

setup_logging()
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Security configuration
if os.getenv('FLASK_ENV') == 'production':
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///orders.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}
db = SQLAlchemy(app)

# Login Manager Configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'
login_manager.login_message = 'Please log in to access the admin panel.'

# UPI Configuration
UPI_ID = os.getenv('UPI_ID', 'yourupi@upi')  # Your UPI ID (e.g., mobile@upi)
PAYEE_NAME = os.getenv('PAYEE_NAME', 'Your Business Name')  # Your business name

# Environment validation
def validate_environment():
    required_vars = ['SECRET_KEY', 'UPI_ID', 'PAYEE_NAME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {missing_vars}")
        if os.getenv('FLASK_ENV') == 'production':
            raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    if os.getenv('FLASK_ENV') == 'production' and os.getenv('SECRET_KEY') == 'dev-secret-key-change-in-production':
        raise ValueError("SECRET_KEY must be changed in production")

try:
    validate_environment()
except ValueError as e:
    logger.error(f"Environment validation failed: {e}")
    if os.getenv('FLASK_ENV') == 'production':
        raise

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    items = db.Column(db.Text, nullable=False)  # JSON string of items
    total_amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='INR')
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, failed
    upi_transaction_id = db.Column(db.String(100))  # UPI transaction ID (manual entry)
    payment_notes = db.Column(db.Text)  # Additional payment notes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'items': json.loads(self.items),
            'total_amount': self.total_amount,
            'currency': self.currency,
            'payment_status': self.payment_status,
            'upi_transaction_id': self.upi_transaction_id,
            'payment_notes': self.payment_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Login Manager User Loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Get active products from database
def get_menu_items():
    products = Product.query.filter_by(is_active=True).all()
    return [product.to_dict() for product in products]


def generate_unique_order_reference():
    now = datetime.utcnow()
    return f"ORD-{now.strftime('%Y%m%d-%H%M%S-%f')}"


@app.route('/')
def index():
    menu_items = get_menu_items()
    return render_template('index.html', menu_items=menu_items)

# Admin Authentication Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('admin_orders'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    return redirect(url_for('admin_orders'))

@app.route('/create_order', methods=['POST'])
def create_order():
    try:
        data = request.get_json()

        required_fields = ['customer_name', 'items']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400

        customer_name = str(data['customer_name']).strip()
        if len(customer_name) < 5 or not customer_name.replace(' ', '').isalpha():
            return jsonify({'error': 'Please enter a valid full name with at least 5 letters and no numbers.'}), 400

        items = data['items']
        total_amount = sum(item['price'] * item['quantity'] for item in items)

        if total_amount <= 0:
            return jsonify({'error': 'Invalid total amount'}), 400

        order_ref = generate_unique_order_reference()
        order = Order(
            customer_name=customer_name,
            items=json.dumps(items),
            total_amount=total_amount,
            payment_notes=f"Order Ref: {order_ref}"
        )
        db.session.add(order)
        db.session.commit()

        return jsonify({
            'order_id': order.id,
            'amount': float(total_amount),
            'currency': 'INR',
            'payee_name': PAYEE_NAME,
            'order_ref': order_ref,
            'customer_name': customer_name,
            'upi_id': UPI_ID
        }), 200
        
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        return jsonify({'error': 'Failed to create order'}), 500

@app.route('/confirm_payment', methods=['POST'])
def confirm_payment():
    try:
        data = request.get_json() or {}
        order_id = data.get('order_id')

        if not order_id:
            return jsonify({'error': 'Order ID is required'}), 400

        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404

        if order.payment_status == 'paid':
            return jsonify({
                'error': 'This order has already been paid and confirmed.',
                'order_id': order.id,
                'status': order.payment_status
            }), 409

        order.payment_status = 'paid'
        order.upi_transaction_id = data.get('transaction_id', '')
        order.payment_notes = data.get('notes', '')
        order.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'status': 'success',
            'order_id': order.id
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error confirming payment: {str(e)}")
        return jsonify({'error': 'Failed to confirm payment'}), 500


@app.route('/order_status/<int:order_id>', methods=['GET'])
def order_status(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    return jsonify({
        'order_id': order.id,
        'status': order.payment_status,
        'customer_name': order.customer_name,
        'total_amount': order.total_amount,
        'updated_at': order.updated_at.isoformat() if order.updated_at else None,
    }), 200


@app.route('/order/<int:order_id>')
def order_details(order_id):
    order = Order.query.get_or_404(order_id)
    items = json.loads(order.items) if order.items else []
    return render_template('order_details.html', order=order, items=items)

# Product Management Routes
@app.route('/admin/products')
@login_required
def admin_products():
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template('admin_products.html', products=products)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        
        if not name or not price:
            flash('Name and price are required', 'error')
            return redirect(url_for('admin_products'))
        
        try:
            product = Product(
                name=name,
                description=description,
                price=float(price)
            )
            db.session.add(product)
            db.session.commit()
            flash('Product added successfully', 'success')
            return redirect(url_for('admin_products'))
        except Exception as e:
            flash(f'Error adding product: {str(e)}', 'error')
    
    return render_template('product_form.html', product=None)

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        is_active = request.form.get('is_active') == 'on'
        
        if not name or not price:
            flash('Name and price are required', 'error')
            return redirect(url_for('edit_product', product_id=product_id))
        
        try:
            product.name = name
            product.description = description
            product.price = float(price)
            product.is_active = is_active
            product.updated_at = datetime.utcnow()
            db.session.commit()
            flash('Product updated successfully', 'success')
            return redirect(url_for('admin_products'))
        except Exception as e:
            flash(f'Error updating product: {str(e)}', 'error')
    
    return render_template('product_form.html', product=product)

@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    try:
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting product: {str(e)}', 'error')
    
    return redirect(url_for('admin_products'))

@app.route('/admin/qr', methods=['GET', 'POST'])
@login_required
def admin_qr_settings():
    qr_path = os.path.join(app.root_path, 'static', 'images', 'upi_qr.png')
    qr_exists = os.path.exists(qr_path)

    if request.method == 'POST':
        file = request.files.get('qr_image')
        if not file or file.filename == '':
            flash('Please choose a QR image to upload.', 'error')
            return redirect(url_for('admin_qr_settings'))

        allowed_exts = {'.png', '.jpg', '.jpeg', '.webp'}
        filename = secure_filename(file.filename)
        ext = os.path.splitext(filename)[1].lower()

        if ext not in allowed_exts:
            flash('Only PNG, JPG, JPEG, and WEBP images are allowed.', 'error')
            return redirect(url_for('admin_qr_settings'))

        os.makedirs(os.path.dirname(qr_path), exist_ok=True)
        file.save(qr_path)
        flash('QR code updated successfully.', 'success')
        return redirect(url_for('admin_qr_settings'))

    return render_template('admin_qr_form.html', qr_exists=qr_exists, qr_url=url_for('static', filename='images/upi_qr.png'))


@app.route('/admin/orders')
@app.route('/admin/orders/')
@login_required
def admin_orders():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    search_term = request.args.get('search_term', '').strip()
    today = datetime.utcnow().strftime('%Y-%m-%d')

    if not start_date and not end_date:
        start_date = today
        end_date = today

    query = Order.query

    if search_term:
        query = query.filter(Order.customer_name.ilike(f'%{search_term}%'))

    if start_date:
        try:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Order.created_at >= start_datetime)
        except ValueError:
            pass

    if end_date:
        try:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Order.created_at < end_datetime)
        except ValueError:
            pass

    orders = query.order_by(Order.created_at.desc()).all()

    total_orders = len(orders)
    total_revenue = sum(order.total_amount for order in orders if order.payment_status == 'paid')
    paid_orders = len([order for order in orders if order.payment_status == 'paid'])
    pending_orders = len([order for order in orders if order.payment_status == 'pending'])

    stats = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'paid_orders': paid_orders,
        'pending_orders': pending_orders
    }

    return render_template('admin_orders.html', orders=orders, stats=stats,
                          start_date=start_date, end_date=end_date,
                          search_term=search_term)


@app.route('/admin/orders/mark-paid', methods=['POST'])
@login_required
def mark_all_paid():
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    search_term = request.form.get('search_term', '').strip()

    query = Order.query

    if search_term:
        query = query.filter(Order.customer_name.ilike(f'%{search_term}%'))

    if start_date:
        try:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Order.created_at >= start_datetime)
        except ValueError:
            pass

    if end_date:
        try:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Order.created_at < end_datetime)
        except ValueError:
            pass

    orders = query.all()
    count = 0
    for order in orders:
        if order.payment_status != 'paid':
            order.payment_status = 'paid'
            order.updated_at = datetime.utcnow()
            count += 1

    if count:
        db.session.commit()
        flash(f'{count} orders marked as paid.', 'success')
    else:
        flash('No orders needed an update.', 'info')

    return redirect(url_for('admin_orders', start_date=start_date, end_date=end_date, search_term=search_term))


@app.route('/admin/orders/edit/<int:order_id>', methods=['GET', 'POST'])
@login_required
def edit_order(order_id):
    order = Order.query.get_or_404(order_id)

    if request.method == 'POST':
        customer_name = request.form.get('customer_name', '').strip()
        payment_status = request.form.get('payment_status', 'pending')
        transaction_id = request.form.get('transaction_id', '').strip()
        payment_notes = request.form.get('payment_notes', '').strip()

        if len(customer_name) < 5 or not customer_name.replace(' ', '').isalpha():
            flash('Please enter a valid full name with at least 5 letters and no numbers.', 'error')
            return redirect(url_for('edit_order', order_id=order_id))

        order.customer_name = customer_name
        order.payment_status = payment_status
        order.upi_transaction_id = transaction_id or order.upi_transaction_id
        order.payment_notes = payment_notes or order.payment_notes
        order.updated_at = datetime.utcnow()

        db.session.commit()
        flash('Order updated successfully', 'success')
        return redirect(url_for('admin_orders'))

    return render_template('admin_order_form.html', order=order)


@app.route('/admin/orders/delete/<int:order_id>', methods=['POST'])
@login_required
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    flash('Order deleted successfully', 'success')
    return redirect(url_for('admin_orders'))

@app.route('/admin/orders/report')
@login_required
def report_preview():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = Order.query

    if start_date:
        try:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Order.created_at >= start_datetime)
        except ValueError:
            pass

    if end_date:
        try:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Order.created_at < end_datetime)
        except ValueError:
            pass

    orders = query.order_by(Order.created_at.desc()).all()

    item_totals = {}
    grand_total = 0.0
    total_paid = 0.0
    total_pending = 0.0

    for order in orders:
        items = json.loads(order.items) if order.items else []
        for item in items:
            item_name = item.get('name', 'Unknown Item')
            quantity = int(item.get('quantity', 0) or 0)
            price = float(item.get('price', 0) or 0)
            line_total = price * quantity

            if item_name not in item_totals:
                item_totals[item_name] = {'quantity': 0, 'total_price': 0.0}

            item_totals[item_name]['quantity'] += quantity
            item_totals[item_name]['total_price'] += line_total
            grand_total += line_total

        if order.payment_status == 'paid':
            total_paid += float(order.total_amount or 0)
        elif order.payment_status == 'pending':
            total_pending += float(order.total_amount or 0)

    return render_template(
        'admin_report.html',
        orders=orders,
        item_totals=item_totals,
        grand_total=grand_total,
        total_paid=total_paid,
        total_pending=total_pending,
        start_date=start_date,
        end_date=end_date
    )


@app.route('/admin/orders/confirm-status', methods=['POST'])
@login_required
def confirm_order_status():
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    updated_count = 0

    for key, value in request.form.items():
        if key.startswith('status_') and value in ['paid', 'pending']:
            try:
                order_id = int(key.replace('status_', ''))
            except ValueError:
                continue

            order = Order.query.get(order_id)
            if order:
                order.payment_status = value
                order.updated_at = datetime.utcnow()
                updated_count += 1

    if updated_count:
        db.session.commit()
        flash(f'{updated_count} order status updated successfully.', 'success')
    else:
        flash('No order status was changed.', 'info')

    return redirect(url_for('report_preview', start_date=start_date, end_date=end_date))


@app.route('/admin/orders/download')
@login_required
def download_orders():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = Order.query

    if start_date:
        try:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Order.created_at >= start_datetime)
        except ValueError:
            pass

    if end_date:
        try:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Order.created_at < end_datetime)
        except ValueError:
            pass

    orders = query.order_by(Order.created_at.desc()).all()

    item_totals = {}
    grand_total = 0.0
    total_paid = 0.0
    total_pending = 0.0

    for order in orders:
        items = json.loads(order.items) if order.items else []
        for item in items:
            item_name = item.get('name', 'Unknown Item')
            quantity = int(item.get('quantity', 0) or 0)
            price = float(item.get('price', 0) or 0)
            line_total = price * quantity

            if item_name not in item_totals:
                item_totals[item_name] = {'quantity': 0, 'total_price': 0.0}

            item_totals[item_name]['quantity'] += quantity
            item_totals[item_name]['total_price'] += line_total
            grand_total += line_total

        if order.payment_status == 'paid':
            total_paid += float(order.total_amount or 0)
        elif order.payment_status == 'pending':
            total_pending += float(order.total_amount or 0)

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(['Sales Report'])
    writer.writerow(['Date Range', f"{start_date or 'All'} to {end_date or 'All'}"])
    writer.writerow(['Grand Total', f"₹{grand_total:.2f}"])
    writer.writerow(['Total Paid', f"₹{total_paid:.2f}"])
    writer.writerow(['Total Pending', f"₹{total_pending:.2f}"])
    writer.writerow([])
    writer.writerow(['Item Name', 'Total Quantity', 'Total Price'])

    if item_totals:
        for item_name, totals in sorted(item_totals.items()):
            writer.writerow([
                item_name,
                totals['quantity'],
                f"₹{totals['total_price']:.2f}"
            ])
    else:
        writer.writerow(['No items found', '', ''])

    writer.writerow([])
    writer.writerow(['Order ID', 'Customer Name', 'Items', 'Total Amount',
                     'Payment Status', 'UPI Transaction ID', 'Payment Notes',
                     'Created At', 'Updated At'])

    for order in orders:
        items = json.loads(order.items) if order.items else []
        items_summary = ', '.join([f"{item['name']} x{item['quantity']}" for item in items])

        writer.writerow([
            order.id,
            order.customer_name,
            items_summary,
            order.total_amount,
            order.payment_status,
            order.upi_transaction_id or '',
            order.payment_notes or '',
            order.created_at.strftime('%Y-%m-%d %H:%M:%S') if order.created_at else '',
            order.updated_at.strftime('%Y-%m-%d %H:%M:%S') if order.updated_at else ''
        ])

    output.seek(0)
    filename = f"orders_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return send_file(
        BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    if request.path.startswith('/admin'):
        return render_template('admin_login.html'), 404
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    logger.error(f"Internal server error: {error}")
    if request.path.startswith('/admin'):
        flash('An internal error occurred', 'error')
        return redirect(url_for('admin_login'))
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(403)
def forbidden_error(error):
    return jsonify({'error': 'Forbidden'}), 403

@app.after_request
def add_security_headers(response):
    if os.getenv('FLASK_ENV') == 'production':
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Create database tables and initialize data
with app.app_context():
    try:
        # Create tables
        db.create_all()
        print("Database tables created successfully")

        admin_username = os.getenv('ADMIN_USERNAME', 'admin')
        admin_password = os.getenv('ADMIN_PASSWORD')
        admin_user = User.query.filter_by(username=admin_username).first()

        if not admin_user:
            admin_user = User(username=admin_username, is_admin=True)
            if admin_password:
                admin_user.set_password(admin_password)
                db.session.add(admin_user)
                db.session.commit()
                print(f"Admin user created (username: {admin_username}) from ADMIN_PASSWORD")
            elif os.getenv('FLASK_ENV') != 'production':
                admin_user.set_password('admin123')
                db.session.add(admin_user)
                db.session.commit()
                print("Default admin user created (username: admin, password: admin123)")
                print("IMPORTANT: Change the default admin password in production!")
            else:
                print("WARNING: No admin user found in production. Set ADMIN_USERNAME and ADMIN_PASSWORD environment variables and restart the app.")
        elif admin_password and not admin_user.check_password(admin_password):
            admin_user.set_password(admin_password)
            db.session.commit()
            print(f"Updated admin password for username: {admin_username}")

        # Create sample products if none exist (only in development)
        if os.getenv('FLASK_ENV') != 'production' and Product.query.count() == 0:
            sample_products = [
                Product(name='Product A', description='High quality product A', price=500),
                Product(name='Product B', description='Premium product B', price=1000),
                Product(name='Product C', description='Standard product C', price=750),
                Product(name='Product D', description='Deluxe product D', price=2000),
            ]
            for product in sample_products:
                db.session.add(product)
            db.session.commit()
            print("Sample products created successfully")

    except Exception as e:
        print(f"Database setup: {e}")

if __name__ == '__main__':
    # Development server
    if os.getenv('FLASK_ENV') != 'production':
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        # Production server (use gunicorn instead)
        app.run(host='0.0.0.0', port=5000)
