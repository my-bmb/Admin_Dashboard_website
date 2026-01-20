# dashboard-website/app.py
import os
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from functools import wraps

import pytz
import cloudinary
import cloudinary.uploader
import cloudinary.api
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Timezone setup
IST = pytz.timezone('Asia/Kolkata')

def ist_now():
    """Get current time in IST"""
    utc_now = datetime.now(pytz.utc)
    return utc_now.astimezone(IST)

def format_ist_datetime(dt, format_str="%d %b %Y, %I:%M %p"):
    """Format datetime in IST"""
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    return dt.astimezone(IST).strftime(format_str)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'admin-dashboard-secret-key-change-me')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Cloudinary configuration
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
    secure=True
)

# Database connection
def get_db_connection():
    """Establish database connection"""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    try:
        conn = psycopg.connect(database_url, row_factory=dict_row)
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

def init_database():
    """Initialize database tables if they don't exist"""
    try:
        logger.info("🔗 Initializing database tables...")
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Create users table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        profile_pic VARCHAR(255),
                        full_name VARCHAR(100) NOT NULL,
                        phone VARCHAR(15) UNIQUE NOT NULL,
                        email VARCHAR(100) UNIQUE NOT NULL,
                        location TEXT NOT NULL,
                        password VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                """)
                logger.info("✅ Table 'users' created successfully")
                
                # Create services table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS services (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        photo VARCHAR(500),
                        price DECIMAL(10, 2) NOT NULL,
                        discount DECIMAL(10, 2) DEFAULT 0,
                        final_price DECIMAL(10, 2) NOT NULL,
                        description TEXT,
                        category VARCHAR(50),
                        status VARCHAR(20) DEFAULT 'active',
                        position INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        cloudinary_id VARCHAR(255)
                    )
                """)
                logger.info("✅ Table 'services' created successfully")
                
                # Create menu table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS menu (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        photo VARCHAR(500),
                        price DECIMAL(10, 2) NOT NULL,
                        discount DECIMAL(10, 2) DEFAULT 0,
                        final_price DECIMAL(10, 2) NOT NULL,
                        description TEXT,
                        category VARCHAR(50),
                        status VARCHAR(20) DEFAULT 'active',
                        position INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        cloudinary_id VARCHAR(255)
                    )
                """)
                logger.info("✅ Table 'menu' created successfully")
                
                # Create cart table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS cart (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                        item_type VARCHAR(10) CHECK (item_type IN ('service', 'menu')),
                        item_id INTEGER NOT NULL,
                        quantity INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, item_type, item_id)
                    )
                """)
                logger.info("✅ Table 'cart' created successfully")
                
                # Create orders table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS orders (
                        order_id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                        user_name VARCHAR(100),
                        user_email VARCHAR(100),
                        user_phone VARCHAR(15),
                        user_address TEXT,
                        items TEXT NOT NULL,
                        total_amount DECIMAL(10, 2) NOT NULL,
                        payment_mode VARCHAR(20) NOT NULL,
                        delivery_location TEXT NOT NULL,
                        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status VARCHAR(20) DEFAULT 'pending',
                        delivery_date TIMESTAMP,
                        notes TEXT
                    )
                """)
                logger.info("✅ Table 'orders' created successfully")
                
                # Create order_items table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS order_items (
                        order_item_id SERIAL PRIMARY KEY,
                        order_id INTEGER REFERENCES orders(order_id) ON DELETE CASCADE,
                        item_type VARCHAR(10) CHECK (item_type IN ('service', 'menu')),
                        item_id INTEGER NOT NULL,
                        item_name VARCHAR(100),
                        item_photo VARCHAR(500),
                        item_description TEXT,
                        quantity INTEGER NOT NULL,
                        price DECIMAL(10, 2) NOT NULL,
                        total DECIMAL(10, 2) NOT NULL
                    )
                """)
                logger.info("✅ Table 'order_items' created successfully")
                
                # Create payments table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS payments (
                        payment_id SERIAL PRIMARY KEY,
                        order_id INTEGER REFERENCES orders(order_id) ON DELETE CASCADE,
                        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                        amount DECIMAL(10, 2) NOT NULL,
                        payment_mode VARCHAR(20) NOT NULL,
                        transaction_id VARCHAR(100),
                        payment_status VARCHAR(20) DEFAULT 'pending',
                        payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        razorpay_order_id VARCHAR(100),
                        razorpay_payment_id VARCHAR(100),
                        razorpay_signature VARCHAR(200)
                    )
                """)
                logger.info("✅ Table 'payments' created successfully")
                
                # Create addresses table WITH google_maps_link
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS addresses (
                        address_id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                        full_name VARCHAR(100) NOT NULL,
                        phone VARCHAR(15) NOT NULL,
                        address_line1 TEXT NOT NULL,
                        address_line2 TEXT,
                        landmark VARCHAR(100),
                        city VARCHAR(50) NOT NULL,
                        state VARCHAR(50) NOT NULL,
                        pincode VARCHAR(10) NOT NULL,
                        latitude DECIMAL(10, 8),
                        longitude DECIMAL(11, 8),
                        google_maps_link TEXT,
                        is_default BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.info("✅ Table 'addresses' created successfully")
                
                # Create reviews table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS reviews (
                        review_id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                        order_id INTEGER REFERENCES orders(order_id) ON DELETE CASCADE,
                        item_type VARCHAR(10) CHECK (item_type IN ('service', 'menu')),
                        item_id INTEGER NOT NULL,
                        rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                        comment TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_approved BOOLEAN DEFAULT FALSE
                    )
                """)
                logger.info("✅ Table 'reviews' created successfully")
                
                # Create notifications table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS notifications (
                        notification_id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                        title VARCHAR(100) NOT NULL,
                        message TEXT NOT NULL,
                        notification_type VARCHAR(20),
                        is_read BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        read_at TIMESTAMP
                    )
                """)
                logger.info("✅ Table 'notifications' created successfully")
                
                # Create admin users table if not exists
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS admin_users (
                        admin_id SERIAL PRIMARY KEY,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        email VARCHAR(100) UNIQUE NOT NULL,
                        password VARCHAR(255) NOT NULL,
                        full_name VARCHAR(100),
                        role VARCHAR(20) DEFAULT 'admin',
                        is_active BOOLEAN DEFAULT TRUE,
                        last_login TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.info("✅ Table 'admin_users' created successfully")
                
                # Check if default admin exists, if not create one
                cur.execute("SELECT * FROM admin_users WHERE username = 'admin'")
                if not cur.fetchone():
                    hashed_password = generate_password_hash('admin123')
                    cur.execute("""
                        INSERT INTO admin_users (username, email, password, full_name, role)
                        VALUES (%s, %s, %s, %s, %s)
                    """, ('admin', 'admin@bitebuddydashboard.com', hashed_password, 'Administrator', 'superadmin'))
                    logger.info("✅ Default admin user created successfully")
                
                conn.commit()
                logger.info("🎉 All database tables initialized successfully")
                
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

# Initialize database on startup
init_database()

# Helper functions
def generate_google_maps_link(latitude, longitude):
    """Generate Google Maps link from latitude and longitude"""
    if latitude and longitude:
        return f"https://www.google.com/maps?q={latitude},{longitude}"
    return None

def update_address_maps_links():
    """Update existing addresses with Google Maps links"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get addresses without maps links
                cur.execute("""
                    SELECT address_id, latitude, longitude 
                    FROM addresses 
                    WHERE google_maps_link IS NULL 
                    AND latitude IS NOT NULL 
                    AND longitude IS NOT NULL
                """)
                
                addresses = cur.fetchall()
                
                for address in addresses:
                    maps_link = generate_google_maps_link(
                        address['latitude'], 
                        address['longitude']
                    )
                    
                    if maps_link:
                        cur.execute("""
                            UPDATE addresses 
                            SET google_maps_link = %s 
                            WHERE address_id = %s
                        """, (maps_link, address['address_id']))
                
                conn.commit()
                logger.info(f"✅ Updated {len(addresses)} addresses with Google Maps links")
                
    except Exception as e:
        logger.error(f"Error updating maps links: {e}")

# Run once on startup
update_address_maps_links()

# Authentication decorator
def admin_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Please login as admin to access this page', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def home():
    if 'admin_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('admin_login'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('admin_login.html')
        
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT * FROM admin_users WHERE username = %s AND is_active = TRUE",
                        (username,)
                    )
                    admin = cur.fetchone()
                    
                    if admin and check_password_hash(admin['password'], password):
                        # Update last login
                        cur.execute(
                            "UPDATE admin_users SET last_login = CURRENT_TIMESTAMP WHERE admin_id = %s",
                            (admin['admin_id'],)
                        )
                        
                        # Set session
                        session['admin_id'] = admin['admin_id']
                        session['username'] = admin['username']
                        session['full_name'] = admin['full_name']
                        session['role'] = admin['role']
                        session['email'] = admin['email']
                        
                        conn.commit()
                        
                        flash('Login successful!', 'success')
                        logger.info(f"Admin '{username}' logged in")
                        return redirect(url_for('dashboard'))
                    else:
                        flash('Invalid username or password', 'error')
                        return render_template('admin_login.html')
                        
        except Exception as e:
            flash(f'Login failed: {str(e)}', 'error')
            logger.error(f"Login error: {e}")
            return render_template('admin_login.html')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    if 'admin_id' in session:
        logger.info(f"Admin '{session.get('username')}' logged out")
        session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('admin_login'))

# Dashboard routes
@app.route('/dashboard')
@admin_login_required
def dashboard():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Total orders count
                cur.execute("SELECT COUNT(*) as total_orders FROM orders")
                total_orders = cur.fetchone()['total_orders']
                
                # Orders by status
                cur.execute("""
                    SELECT status, COUNT(*) as count 
                    FROM orders 
                    GROUP BY status
                """)
                status_counts = {row['status']: row['count'] for row in cur.fetchall()}
                
                # Today's orders (IST date)
                today_start = ist_now().replace(hour=0, minute=0, second=0, microsecond=0)
                today_end = today_start + timedelta(days=1)
                
                cur.execute("""
                    SELECT COUNT(*) as today_orders, 
                           COALESCE(SUM(total_amount), 0) as today_revenue
                    FROM orders 
                    WHERE order_date >= %s AND order_date < %s
                """, (today_start.astimezone(pytz.utc), today_end.astimezone(pytz.utc)))
                today_data = cur.fetchone()
                
                # Total revenue
                cur.execute("""
                    SELECT COALESCE(SUM(total_amount), 0) as total_revenue 
                    FROM orders 
                    WHERE status != 'cancelled'
                """)
                total_revenue = cur.fetchone()['total_revenue']
                
                # Active users count
                cur.execute("SELECT COUNT(*) as active_users FROM users WHERE is_active = TRUE")
                active_users = cur.fetchone()['active_users']
                
                # Pending payments
                cur.execute("""
                    SELECT COUNT(*) as pending_payments 
                    FROM payments 
                    WHERE payment_status = 'pending'
                """)
                pending_payments = cur.fetchone()['pending_payments']
                
                # Latest orders (last 10)
                cur.execute("""
                    SELECT 
                        o.order_id,
                        o.user_name,
                        o.total_amount,
                        o.status,
                        o.order_date,
                        o.payment_mode,
                        u.phone as user_phone
                    FROM orders o
                    LEFT JOIN users u ON o.user_id = u.id
                    ORDER BY o.order_date DESC
                    LIMIT 10
                """)
                latest_orders = cur.fetchall()
                
                # Format dates for display
                for order in latest_orders:
                    order['order_date_formatted'] = format_ist_datetime(order['order_date'])
                
                # Top selling services
                cur.execute("""
                    SELECT 
                        s.name,
                        COUNT(oi.order_item_id) as sales_count,
                        SUM(oi.quantity) as total_quantity,
                        SUM(oi.total) as total_revenue
                    FROM order_items oi
                    JOIN services s ON oi.item_id = s.id AND oi.item_type = 'service'
                    GROUP BY s.id, s.name
                    ORDER BY total_revenue DESC
                    LIMIT 5
                """)
                top_services = cur.fetchall()
                
                # Top selling menu items
                cur.execute("""
                    SELECT 
                        m.name,
                        COUNT(oi.order_item_id) as sales_count,
                        SUM(oi.quantity) as total_quantity,
                        SUM(oi.total) as total_revenue
                    FROM order_items oi
                    JOIN menu m ON oi.item_id = m.id AND oi.item_type = 'menu'
                    GROUP BY m.id, m.name
                    ORDER BY total_revenue DESC
                    LIMIT 5
                """)
                top_menu = cur.fetchall()
                
                # Daily revenue for last 7 days
                cur.execute("""
                    SELECT 
                        DATE(order_date AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') as order_day,
                        COUNT(*) as order_count,
                        COALESCE(SUM(total_amount), 0) as daily_revenue
                    FROM orders
                    WHERE order_date >= CURRENT_DATE - INTERVAL '7 days'
                    GROUP BY DATE(order_date AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata')
                    ORDER BY order_day
                """)
                daily_revenue_data = cur.fetchall()
                
                # Prepare chart data
                chart_labels = []
                chart_revenue = []
                chart_orders = []
                
                for data in daily_revenue_data:
                    chart_labels.append(data['order_day'].strftime('%b %d'))
                    chart_revenue.append(float(data['daily_revenue']))
                    chart_orders.append(data['order_count'])
                
                # Monthly revenue
                cur.execute("""
                    SELECT 
                        TO_CHAR(order_date, 'Mon YYYY') as month,
                        COUNT(*) as order_count,
                        COALESCE(SUM(total_amount), 0) as monthly_revenue
                    FROM orders
                    WHERE order_date >= CURRENT_DATE - INTERVAL '6 months'
                    GROUP BY TO_CHAR(order_date, 'Mon YYYY'), 
                             DATE_TRUNC('month', order_date)
                    ORDER BY DATE_TRUNC('month', order_date)
                    LIMIT 6
                """)
                monthly_data = cur.fetchall()
                
                monthly_labels = []
                monthly_revenue = []
                
                for data in monthly_data:
                    monthly_labels.append(data['month'])
                    monthly_revenue.append(float(data['monthly_revenue']))
        
        return render_template('dashboard/index.html',
                           total_orders=total_orders,
                           status_counts=status_counts,
                           today_orders=today_data['today_orders'],
                           today_revenue=float(today_data['today_revenue']),
                           total_revenue=float(total_revenue),
                           active_users=active_users,
                           pending_payments=pending_payments,
                           latest_orders=latest_orders,
                           top_services=top_services,
                           top_menu=top_menu,
                           chart_labels=chart_labels,
                           chart_revenue=chart_revenue,
                           chart_orders=chart_orders,
                           monthly_labels=monthly_labels,
                           monthly_revenue=monthly_revenue)
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('dashboard/index.html',
                           total_orders=0,
                           status_counts={},
                           today_orders=0,
                           today_revenue=0,
                           total_revenue=0,
                           active_users=0,
                           pending_payments=0,
                           latest_orders=[],
                           top_services=[],
                           top_menu=[],
                           chart_labels=[],
                           chart_revenue=[],
                           chart_orders=[],
                           monthly_labels=[],
                           monthly_revenue=[])

# Orders management
@app.route('/dashboard/orders')
@admin_login_required
def orders_list():
    try:
        status = request.args.get('status', 'all')
        page = int(request.args.get('page', 1))
        per_page = 20
        offset = (page - 1) * per_page
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Build query based on status
                query = """
                    SELECT 
                        o.*,
                        u.phone as user_phone,
                        u.email as user_email,
                        p.payment_status,
                        p.payment_mode as actual_payment_mode
                    FROM orders o
                    LEFT JOIN users u ON o.user_id = u.id
                    LEFT JOIN payments p ON o.order_id = p.order_id
                """
                
                params = []
                
                if status != 'all':
                    query += " WHERE o.status = %s"
                    params.append(status)
                
                query += " ORDER BY o.order_date DESC LIMIT %s OFFSET %s"
                params.extend([per_page, offset])
                
                cur.execute(query, params)
                orders = cur.fetchall()
                
                # Count total orders for pagination
                count_query = "SELECT COUNT(*) as total FROM orders"
                count_params = []
                
                if status != 'all':
                    count_query += " WHERE status = %s"
                    count_params.append(status)
                
                cur.execute(count_query, count_params)
                total_orders = cur.fetchone()['total']
                total_pages = (total_orders + per_page - 1) // per_page
                
                # Format dates
                for order in orders:
                    order['order_date_formatted'] = format_ist_datetime(order['order_date'])
                    if order.get('delivery_date'):
                        order['delivery_date_formatted'] = format_ist_datetime(order['delivery_date'])
                    else:
                        order['delivery_date_formatted'] = None
                    
                    # Parse items JSON for item count
                    try:
                        items = json.loads(order['items'])
                        order['item_count'] = len(items)
                    except:
                        order['item_count'] = 0
        
        return render_template('orders/list.html',
                           orders=orders,
                           status=status,
                           page=page,
                           total_pages=total_pages,
                           total_orders=total_orders)
        
    except Exception as e:
        logger.error(f"Orders list error: {e}")
        flash(f'Error loading orders: {str(e)}', 'error')
        return render_template('orders/list.html',
                           orders=[],
                           status='all',
                           page=1,
                           total_pages=0,
                           total_orders=0)

@app.route('/dashboard/orders/<int:order_id>')
@admin_login_required
def order_detail(order_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get order details
                cur.execute("""
                    SELECT 
                        o.*,
                        u.phone as user_phone,
                        u.email as user_email,
                        u.profile_pic as user_profile_pic,
                        p.*
                    FROM orders o
                    LEFT JOIN users u ON o.user_id = u.id
                    LEFT JOIN payments p ON o.order_id = p.order_id
                    WHERE o.order_id = %s
                """, (order_id,))
                
                order = cur.fetchone()
                
                if not order:
                    flash('Order not found', 'error')
                    return redirect(url_for('orders_list'))
                
                # Get order items
                cur.execute("""
                    SELECT * FROM order_items 
                    WHERE order_id = %s
                    ORDER BY order_item_id
                """, (order_id,))
                
                order_items = cur.fetchall()
                
                # If no items in order_items table, parse from JSON
                if not order_items and order['items']:
                    try:
                        items_json = json.loads(order['items'])
                        for item in items_json:
                            order_items.append({
                                'item_name': item.get('item_name', item.get('name', 'Unknown')),
                                'item_type': item.get('item_type', item.get('type', 'unknown')),
                                'quantity': item.get('quantity', 1),
                                'price': float(item.get('price', 0)),
                                'total': float(item.get('total', 0)),
                                'item_description': item.get('item_description', item.get('description', '')),
                                'item_photo': item.get('item_photo', item.get('photo', ''))
                            })
                    except Exception as e:
                        logger.error(f"Error parsing items JSON: {e}")
                
                # Format dates
                order['order_date_formatted'] = format_ist_datetime(order['order_date'])
                if order.get('delivery_date'):
                    order['delivery_date_formatted'] = format_ist_datetime(order['delivery_date'])
                
                if order.get('payment_date'):
                    order['payment_date_formatted'] = format_ist_datetime(order['payment_date'])
        
        return render_template('orders/detail.html',
                           order=order,
                           order_items=order_items)
        
    except Exception as e:
        logger.error(f"Order detail error: {e}")
        flash(f'Error loading order details: {str(e)}', 'error')
        return redirect(url_for('orders_list'))

@app.route('/dashboard/orders/<int:order_id>/update-status', methods=['POST'])
@admin_login_required
def update_order_status(order_id):
    try:
        new_status = request.form.get('status', '').strip()
        notes = request.form.get('notes', '').strip()
        
        if not new_status:
            return jsonify({'success': False, 'message': 'Status is required'})
        
        valid_statuses = ['pending', 'confirmed', 'processing', 'out_for_delivery', 'delivered', 'cancelled']
        if new_status not in valid_statuses:
            return jsonify({'success': False, 'message': 'Invalid status'})
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check if order exists
                cur.execute("SELECT order_id FROM orders WHERE order_id = %s", (order_id,))
                if not cur.fetchone():
                    return jsonify({'success': False, 'message': 'Order not found'})
                
                # Update order status
                update_query = "UPDATE orders SET status = %s"
                params = [new_status]
                
                # If delivered, set delivery date
                if new_status == 'delivered':
                    update_query += ", delivery_date = %s"
                    params.append(ist_now())
                
                # If cancelled, update payment status
                if new_status == 'cancelled':
                    cur.execute("""
                        UPDATE payments 
                        SET payment_status = 'refunded' 
                        WHERE order_id = %s
                    """, (order_id,))
                
                update_query += " WHERE order_id = %s"
                params.append(order_id)
                
                cur.execute(update_query, params)
                
                # Add notification for user
                try:
                    cur.execute("""
                        SELECT user_id FROM orders WHERE order_id = %s
                    """, (order_id,))
                    user_result = cur.fetchone()
                    
                    if user_result:
                        user_id = user_result['user_id']
                        cur.execute("""
                            INSERT INTO notifications 
                            (user_id, title, message, notification_type)
                            VALUES (%s, %s, %s, %s)
                        """, (
                            user_id,
                            f'Order #{order_id} Status Update',
                            f'Your order status has been updated to: {new_status}',
                            'order_update'
                        ))
                except Exception as e:
                    logger.error(f"Notification error: {e}")
                
                conn.commit()
                
                logger.info(f"Order #{order_id} status updated to '{new_status}' by admin {session.get('username')}")
                
                return jsonify({
                    'success': True,
                    'message': f'Order status updated to {new_status}',
                    'new_status': new_status
                })
                
    except Exception as e:
        logger.error(f"Update order status error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Users management
@app.route('/dashboard/users')
@admin_login_required
def users_list():
    try:
        page = int(request.args.get('page', 1))
        per_page = 20
        offset = (page - 1) * per_page
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get users
                cur.execute("""
                    SELECT 
                        u.*,
                        COUNT(o.order_id) as order_count,
                        COALESCE(SUM(o.total_amount), 0) as total_spent,
                        MAX(o.order_date) as last_order_date
                    FROM users u
                    LEFT JOIN orders o ON u.id = o.user_id
                    GROUP BY u.id
                    ORDER BY u.created_at DESC
                    LIMIT %s OFFSET %s
                """, (per_page, offset))
                
                users = cur.fetchall()
                
                # Count total users
                cur.execute("SELECT COUNT(*) as total FROM users")
                total_users = cur.fetchone()['total']
                total_pages = (total_users + per_page - 1) // per_page
                
                # Format dates
                for user in users:
                    user['created_at_formatted'] = format_ist_datetime(user['created_at'])
                    if user['last_login']:
                        user['last_login_formatted'] = format_ist_datetime(user['last_login'])
                    if user['last_order_date']:
                        user['last_order_date_formatted'] = format_ist_datetime(user['last_order_date'])
        
        return render_template('users/list.html',
                           users=users,
                           page=page,
                           total_pages=total_pages,
                           total_users=total_users)
        
    except Exception as e:
        logger.error(f"Users list error: {e}")
        flash(f'Error loading users: {str(e)}', 'error')
        return render_template('users/list.html',
                           users=[],
                           page=1,
                           total_pages=0,
                           total_users=0)

@app.route('/dashboard/users/<int:user_id>')
@admin_login_required
def user_detail(user_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get user details
                cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                user = cur.fetchone()
                
                if not user:
                    flash('User not found', 'error')
                    return redirect(url_for('users_list'))
                
                # Get user's orders
                cur.execute("""
                    SELECT * FROM orders 
                    WHERE user_id = %s 
                    ORDER BY order_date DESC
                    LIMIT 10
                """, (user_id,))
                
                orders = cur.fetchall()
                
                # Get user's addresses
                cur.execute("""
                    SELECT * FROM addresses 
                    WHERE user_id = %s 
                    ORDER BY is_default DESC, created_at DESC
                """, (user_id,))
                
                addresses = cur.fetchall()
                
                # Get user's cart items
                cur.execute("""
                    SELECT 
                        c.*,
                        COALESCE(s.name, m.name) as item_name,
                        COALESCE(s.final_price, m.final_price) as item_price
                    FROM cart c
                    LEFT JOIN services s ON c.item_type = 'service' AND c.item_id = s.id
                    LEFT JOIN menu m ON c.item_type = 'menu' AND c.item_id = m.id
                    WHERE c.user_id = %s
                """, (user_id,))
                
                cart_items = cur.fetchall()
                
                # Format dates
                user['created_at_formatted'] = format_ist_datetime(user['created_at'])
                if user['last_login']:
                    user['last_login_formatted'] = format_ist_datetime(user['last_login'])
                
                for order in orders:
                    order['order_date_formatted'] = format_ist_datetime(order['order_date'])
                
                for address in addresses:
                    address['created_at_formatted'] = format_ist_datetime(address['created_at'])
        
        return render_template('users/detail.html',
                           user=user,
                           orders=orders,
                           addresses=addresses,
                           cart_items=cart_items)
        
    except Exception as e:
        logger.error(f"User detail error: {e}")
        flash(f'Error loading user details: {str(e)}', 'error')
        return redirect(url_for('users_list'))

@app.route('/dashboard/users/<int:user_id>/toggle-active', methods=['POST'])
@admin_login_required
def toggle_user_active(user_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get current status
                cur.execute("SELECT is_active FROM users WHERE id = %s", (user_id,))
                user = cur.fetchone()
                
                if not user:
                    return jsonify({'success': False, 'message': 'User not found'})
                
                new_status = not user['is_active']
                
                # Update status
                cur.execute("""
                    UPDATE users SET is_active = %s WHERE id = %s
                """, (new_status, user_id))
                
                conn.commit()
                
                action = "activated" if new_status else "deactivated"
                logger.info(f"User #{user_id} {action} by admin {session.get('username')}")
                
                return jsonify({
                    'success': True,
                    'message': f'User {action} successfully',
                    'is_active': new_status
                })
                
    except Exception as e:
        logger.error(f"Toggle user active error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Services management
@app.route('/dashboard/services')
@admin_login_required
def services_list():
    try:
        category = request.args.get('category', 'all')
        status = request.args.get('status', 'active')
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Build query
                query = "SELECT * FROM services WHERE 1=1"
                params = []
                
                if category != 'all':
                    query += " AND category = %s"
                    params.append(category)
                
                if status != 'all':
                    query += " AND status = %s"
                    params.append(status)
                
                query += " ORDER BY position, name"
                
                cur.execute(query, params)
                services = cur.fetchall()
                
                # Get unique categories
                cur.execute("SELECT DISTINCT category FROM services WHERE category IS NOT NULL ORDER BY category")
                categories = [row['category'] for row in cur.fetchall()]
        
        return render_template('services/list.html',
                           services=services,
                           categories=categories,
                           selected_category=category,
                           selected_status=status)
        
    except Exception as e:
        logger.error(f"Services list error: {e}")
        flash(f'Error loading services: {str(e)}', 'error')
        return render_template('services/list.html',
                           services=[],
                           categories=[],
                           selected_category='all',
                           selected_status='active')

@app.route('/dashboard/services/add', methods=['GET', 'POST'])
@admin_login_required
def add_service():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            price = request.form.get('price', '0').strip()
            discount = request.form.get('discount', '0').strip()
            description = request.form.get('description', '').strip()
            category = request.form.get('category', '').strip()
            status = request.form.get('status', 'active').strip()
            
            # Validation
            errors = []
            if not name:
                errors.append('Service name is required')
            if not price or float(price) <= 0:
                errors.append('Valid price is required')
            
            if errors:
                for error in errors:
                    flash(error, 'error')
                return redirect(url_for('add_service'))
            
            # Calculate final price
            price_val = Decimal(price)
            discount_val = Decimal(discount) if discount else Decimal('0')
            final_price = price_val - discount_val
            
            if final_price < 0:
                final_price = Decimal('0')
            
            cloudinary_id = None
            photo_url = None
            
            # Handle photo upload
            if 'photo' in request.files and request.files['photo'].filename:
                file = request.files['photo']
                if file and file.filename:
                    try:
                        # Upload to Cloudinary
                        result = cloudinary.uploader.upload(
                            file,
                            folder="services",
                            public_id=f"service_{name.lower().replace(' ', '_')}_{int(datetime.now().timestamp())}",
                            overwrite=True,
                            transformation=[
                                {'width': 800, 'height': 600, 'crop': 'fill'},
                                {'quality': 'auto', 'fetch_format': 'auto'}
                            ]
                        )
                        
                        photo_url = result['secure_url']
                        cloudinary_id = result['public_id']
                        
                    except Exception as upload_error:
                        logger.error(f"Cloudinary upload error: {upload_error}")
                        flash('Photo upload failed, service added without photo', 'warning')
            
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get max position
                    cur.execute("SELECT COALESCE(MAX(position), 0) as max_pos FROM services")
                    max_pos = cur.fetchone()['max_pos']
                    new_position = max_pos + 1
                    
                    # Insert service
                    cur.execute("""
                        INSERT INTO services 
                        (name, photo, price, discount, final_price, description, 
                         category, status, position, cloudinary_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (name, photo_url, price_val, discount_val, final_price, 
                          description, category, status, new_position, cloudinary_id))
                    
                    conn.commit()
                    
                    logger.info(f"Service '{name}' added by admin {session.get('username')}")
                    flash('Service added successfully!', 'success')
                    return redirect(url_for('services_list'))
                    
        except Exception as e:
            logger.error(f"Add service error: {e}")
            flash(f'Error adding service: {str(e)}', 'error')
            return redirect(url_for('add_service'))
    
    return render_template('services/add_edit.html', service=None, action='add')

@app.route('/dashboard/services/<int:service_id>/edit', methods=['GET', 'POST'])
@admin_login_required
def edit_service(service_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                if request.method == 'GET':
                    # Get service details
                    cur.execute("SELECT * FROM services WHERE id = %s", (service_id,))
                    service = cur.fetchone()
                    
                    if not service:
                        flash('Service not found', 'error')
                        return redirect(url_for('services_list'))
                    
                    return render_template('services/add_edit.html', service=service, action='edit')
                
                else:  # POST request
                    # Get form data
                    name = request.form.get('name', '').strip()
                    price = request.form.get('price', '0').strip()
                    discount = request.form.get('discount', '0').strip()
                    description = request.form.get('description', '').strip()
                    category = request.form.get('category', '').strip()
                    status = request.form.get('status', 'active').strip()
                    
                    # Validation
                    errors = []
                    if not name:
                        errors.append('Service name is required')
                    if not price or float(price) <= 0:
                        errors.append('Valid price is required')
                    
                    if errors:
                        for error in errors:
                            flash(error, 'error')
                        return redirect(url_for('edit_service', service_id=service_id))
                    
                    # Calculate final price
                    price_val = Decimal(price)
                    discount_val = Decimal(discount) if discount else Decimal('0')
                    final_price = price_val - discount_val
                    
                    if final_price < 0:
                        final_price = Decimal('0')
                    
                    # Handle photo upload
                    current_photo = None
                    current_cloudinary_id = None
                    
                    # Get current photo details
                    cur.execute("SELECT photo, cloudinary_id FROM services WHERE id = %s", (service_id,))
                    current = cur.fetchone()
                    if current:
                        current_photo = current['photo']
                        current_cloudinary_id = current['cloudinary_id']
                    
                    photo_url = current_photo
                    cloudinary_id = current_cloudinary_id
                    
                    if 'photo' in request.files and request.files['photo'].filename:
                        file = request.files['photo']
                        if file and file.filename:
                            try:
                                # Delete old photo from Cloudinary if exists
                                if current_cloudinary_id:
                                    try:
                                        cloudinary.uploader.destroy(current_cloudinary_id)
                                    except Exception as delete_error:
                                        logger.warning(f"Could not delete old photo: {delete_error}")
                                
                                # Upload new photo
                                result = cloudinary.uploader.upload(
                                    file,
                                    folder="services",
                                    public_id=f"service_{name.lower().replace(' ', '_')}_{int(datetime.now().timestamp())}",
                                    overwrite=True,
                                    transformation=[
                                        {'width': 800, 'height': 600, 'crop': 'fill'},
                                        {'quality': 'auto', 'fetch_format': 'auto'}
                                    ]
                                )
                                
                                photo_url = result['secure_url']
                                cloudinary_id = result['public_id']
                                
                            except Exception as upload_error:
                                logger.error(f"Cloudinary upload error: {upload_error}")
                                flash('Photo upload failed, using existing photo', 'warning')
                    
                    # Check if remove photo was requested
                    if request.form.get('remove_photo') == 'yes' and current_cloudinary_id:
                        try:
                            cloudinary.uploader.destroy(current_cloudinary_id)
                        except Exception as delete_error:
                            logger.warning(f"Could not delete photo: {delete_error}")
                        
                        photo_url = None
                        cloudinary_id = None
                    
                    # Update service
                    cur.execute("""
                        UPDATE services 
                        SET name = %s, 
                            photo = %s, 
                            price = %s, 
                            discount = %s, 
                            final_price = %s, 
                            description = %s, 
                            category = %s, 
                            status = %s,
                            cloudinary_id = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (name, photo_url, price_val, discount_val, final_price, 
                          description, category, status, cloudinary_id, service_id))
                    
                    conn.commit()
                    
                    logger.info(f"Service #{service_id} updated by admin {session.get('username')}")
                    flash('Service updated successfully!', 'success')
                    return redirect(url_for('services_list'))
                    
    except Exception as e:
        logger.error(f"Edit service error: {e}")
        flash(f'Error updating service: {str(e)}', 'error')
        return redirect(url_for('services_list'))

@app.route('/dashboard/services/<int:service_id>/delete', methods=['POST'])
@admin_login_required
def delete_service(service_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check if service exists
                cur.execute("SELECT name, cloudinary_id FROM services WHERE id = %s", (service_id,))
                service = cur.fetchone()
                
                if not service:
                    return jsonify({'success': False, 'message': 'Service not found'})
                
                # Delete from Cloudinary
                if service['cloudinary_id']:
                    try:
                        cloudinary.uploader.destroy(service['cloudinary_id'])
                    except Exception as delete_error:
                        logger.warning(f"Could not delete Cloudinary photo: {delete_error}")
                
                # Delete service
                cur.execute("DELETE FROM services WHERE id = %s", (service_id,))
                conn.commit()
                
                logger.info(f"Service #{service_id} deleted by admin {session.get('username')}")
                
                return jsonify({
                    'success': True,
                    'message': f"Service '{service['name']}' deleted successfully"
                })
                
    except Exception as e:
        logger.error(f"Delete service error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Menu management (similar to services)
@app.route('/dashboard/menu')
@admin_login_required
def menu_list():
    try:
        category = request.args.get('category', 'all')
        status = request.args.get('status', 'active')
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Build query
                query = "SELECT * FROM menu WHERE 1=1"
                params = []
                
                if category != 'all':
                    query += " AND category = %s"
                    params.append(category)
                
                if status != 'all':
                    query += " AND status = %s"
                    params.append(status)
                
                query += " ORDER BY position, name"
                
                cur.execute(query, params)
                menu_items = cur.fetchall()
                
                # Get unique categories
                cur.execute("SELECT DISTINCT category FROM menu WHERE category IS NOT NULL ORDER BY category")
                categories = [row['category'] for row in cur.fetchall()]
        
        return render_template('menu/list.html',
                           menu_items=menu_items,
                           categories=categories,
                           selected_category=category,
                           selected_status=status)
        
    except Exception as e:
        logger.error(f"Menu list error: {e}")
        flash(f'Error loading menu items: {str(e)}', 'error')
        return render_template('menu/list.html',
                           menu_items=[],
                           categories=[],
                           selected_category='all',
                           selected_status='active')

# Analytics API endpoints
@app.route('/api/dashboard/stats')
@admin_login_required
def api_dashboard_stats():
    try:
        period = request.args.get('period', 'today')  # today, week, month, year
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Date filters based on period
                now = ist_now()
                
                if period == 'today':
                    start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    end_date = start_date + timedelta(days=1)
                elif period == 'week':
                    start_date = now - timedelta(days=now.weekday())
                    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    end_date = start_date + timedelta(days=7)
                elif period == 'month':
                    start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    if now.month == 12:
                        end_date = now.replace(year=now.year+1, month=1, day=1)
                    else:
                        end_date = now.replace(month=now.month+1, day=1)
                elif period == 'year':
                    start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                    end_date = now.replace(year=now.year+1, month=1, day=1)
                else:
                    start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    end_date = start_date + timedelta(days=1)
                
                # Convert to UTC for database query
                start_date_utc = start_date.astimezone(pytz.utc)
                end_date_utc = end_date.astimezone(pytz.utc)
                
                # Orders count
                cur.execute("""
                    SELECT COUNT(*) as order_count 
                    FROM orders 
                    WHERE order_date >= %s AND order_date < %s
                """, (start_date_utc, end_date_utc))
                order_count = cur.fetchone()['order_count']
                
                # Revenue
                cur.execute("""
                    SELECT COALESCE(SUM(total_amount), 0) as revenue 
                    FROM orders 
                    WHERE order_date >= %s AND order_date < %s 
                    AND status != 'cancelled'
                """, (start_date_utc, end_date_utc))
                revenue = float(cur.fetchone()['revenue'])
                
                # Average order value
                avg_order_value = revenue / order_count if order_count > 0 else 0
                
                # New customers
                cur.execute("""
                    SELECT COUNT(*) as new_customers 
                    FROM users 
                    WHERE created_at >= %s AND created_at < %s
                """, (start_date_utc, end_date_utc))
                new_customers = cur.fetchone()['new_customers']
                
                # Order status breakdown
                cur.execute("""
                    SELECT 
                        status,
                        COUNT(*) as count,
                        COALESCE(SUM(total_amount), 0) as amount
                    FROM orders 
                    WHERE order_date >= %s AND order_date < %s
                    GROUP BY status
                """, (start_date_utc, end_date_utc))
                
                status_data = cur.fetchall()
                status_breakdown = {}
                for row in status_data:
                    status_breakdown[row['status']] = {
                        'count': row['count'],
                        'amount': float(row['amount'])
                    }
                
                # Payment method breakdown
                cur.execute("""
                    SELECT 
                        payment_mode,
                        COUNT(*) as count,
                        COALESCE(SUM(total_amount), 0) as amount
                    FROM orders 
                    WHERE order_date >= %s AND order_date < %s
                    GROUP BY payment_mode
                """, (start_date_utc, end_date_utc))
                
                payment_data = cur.fetchall()
                payment_breakdown = {}
                for row in payment_data:
                    payment_breakdown[row['payment_mode']] = {
                        'count': row['count'],
                        'amount': float(row['amount'])
                    }
                
                return jsonify({
                    'success': True,
                    'period': period,
                    'stats': {
                        'order_count': order_count,
                        'revenue': revenue,
                        'avg_order_value': avg_order_value,
                        'new_customers': new_customers
                    },
                    'status_breakdown': status_breakdown,
                    'payment_breakdown': payment_breakdown,
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d')
                })
                
    except Exception as e:
        logger.error(f"API stats error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/dashboard/chart/revenue')
@admin_login_required
def api_revenue_chart():
    try:
        chart_type = request.args.get('type', 'daily')  # daily, weekly, monthly
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                if chart_type == 'daily':
                    # Last 30 days
                    cur.execute("""
                        SELECT 
                            DATE(order_date AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') as date,
                            COUNT(*) as order_count,
                            COALESCE(SUM(total_amount), 0) as revenue
                        FROM orders
                        WHERE order_date >= CURRENT_DATE - INTERVAL '30 days'
                        GROUP BY DATE(order_date AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata')
                        ORDER BY date
                    """)
                    
                    data = cur.fetchall()
                    
                    labels = [row['date'].strftime('%b %d') for row in data]
                    revenue = [float(row['revenue']) for row in data]
                    order_counts = [row['order_count'] for row in data]
                    
                elif chart_type == 'weekly':
                    # Last 12 weeks
                    cur.execute("""
                        SELECT 
                            DATE_TRUNC('week', order_date AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') as week_start,
                            COUNT(*) as order_count,
                            COALESCE(SUM(total_amount), 0) as revenue
                        FROM orders
                        WHERE order_date >= CURRENT_DATE - INTERVAL '12 weeks'
                        GROUP BY DATE_TRUNC('week', order_date AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata')
                        ORDER BY week_start
                    """)
                    
                    data = cur.fetchall()
                    
                    labels = [row['week_start'].strftime('%b %d') for row in data]
                    revenue = [float(row['revenue']) for row in data]
                    order_counts = [row['order_count'] for row in data]
                    
                else:  # monthly
                    # Last 12 months
                    cur.execute("""
                        SELECT 
                            DATE_TRUNC('month', order_date AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') as month_start,
                            TO_CHAR(order_date, 'Mon YYYY') as month_name,
                            COUNT(*) as order_count,
                            COALESCE(SUM(total_amount), 0) as revenue
                        FROM orders
                        WHERE order_date >= CURRENT_DATE - INTERVAL '12 months'
                        GROUP BY DATE_TRUNC('month', order_date AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata'), 
                                 TO_CHAR(order_date, 'Mon YYYY')
                        ORDER BY month_start
                    """)
                    
                    data = cur.fetchall()
                    
                    labels = [row['month_name'] for row in data]
                    revenue = [float(row['revenue']) for row in data]
                    order_counts = [row['order_count'] for row in data]
                
                return jsonify({
                    'success': True,
                    'chart_type': chart_type,
                    'labels': labels,
                    'datasets': {
                        'revenue': revenue,
                        'orders': order_counts
                    }
                })
                
    except Exception as e:
        logger.error(f"Revenue chart error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Address management with Google Maps links
@app.route('/dashboard/addresses')
@admin_login_required
def addresses_list():
    try:
        page = int(request.args.get('page', 1))
        per_page = 20
        offset = (page - 1) * per_page
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get addresses with user info
                cur.execute("""
                    SELECT 
                        a.*,
                        u.full_name as user_name,
                        u.phone as user_phone,
                        u.email as user_email
                    FROM addresses a
                    JOIN users u ON a.user_id = u.id
                    ORDER BY a.created_at DESC
                    LIMIT %s OFFSET %s
                """, (per_page, offset))
                
                addresses = cur.fetchall()
                
                # Generate Google Maps links for addresses without them
                for address in addresses:
                    if not address['google_maps_link'] and address['latitude'] and address['longitude']:
                        address['google_maps_link'] = generate_google_maps_link(
                            address['latitude'], 
                            address['longitude']
                        )
                
                # Count total addresses
                cur.execute("SELECT COUNT(*) as total FROM addresses")
                total_addresses = cur.fetchone()['total']
                total_pages = (total_addresses + per_page - 1) // per_page
        
        return render_template('addresses/list.html',
                           addresses=addresses,
                           page=page,
                           total_pages=total_pages,
                           total_addresses=total_addresses)
        
    except Exception as e:
        logger.error(f"Addresses list error: {e}")
        flash(f'Error loading addresses: {str(e)}', 'error')
        return render_template('addresses/list.html',
                           addresses=[],
                           page=1,
                           total_pages=0,
                           total_addresses=0)

# Payments management
@app.route('/dashboard/payments')
@admin_login_required
def payments_list():
    try:
        status = request.args.get('status', 'all')
        page = int(request.args.get('page', 1))
        per_page = 20
        offset = (page - 1) * per_page
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Build query
                query = """
                    SELECT 
                        p.*,
                        o.order_id,
                        o.total_amount,
                        o.status as order_status,
                        u.full_name as user_name,
                        u.phone as user_phone
                    FROM payments p
                    JOIN orders o ON p.order_id = o.order_id
                    JOIN users u ON p.user_id = u.id
                """
                
                params = []
                
                if status != 'all':
                    query += " WHERE p.payment_status = %s"
                    params.append(status)
                
                query += " ORDER BY p.payment_date DESC LIMIT %s OFFSET %s"
                params.extend([per_page, offset])
                
                cur.execute(query, params)
                payments = cur.fetchall()
                
                # Count total payments
                count_query = "SELECT COUNT(*) as total FROM payments"
                count_params = []
                
                if status != 'all':
                    count_query += " WHERE payment_status = %s"
                    count_params.append(status)
                
                cur.execute(count_query, count_params)
                total_payments = cur.fetchone()['total']
                total_pages = (total_payments + per_page - 1) // per_page
                
                # Format dates
                for payment in payments:
                    payment['payment_date_formatted'] = format_ist_datetime(payment['payment_date'])
        
        return render_template('payments/list.html',
                           payments=payments,
                           status=status,
                           page=page,
                           total_pages=total_pages,
                           total_payments=total_payments)
        
    except Exception as e:
        logger.error(f"Payments list error: {e}")
        flash(f'Error loading payments: {str(e)}', 'error')
        return render_template('payments/list.html',
                           payments=[],
                           status='all',
                           page=1,
                           total_pages=0,
                           total_payments=0)

# Reviews management
@app.route('/dashboard/reviews')
@admin_login_required
def reviews_list():
    try:
        approved = request.args.get('approved', 'all')  # all, yes, no
        page = int(request.args.get('page', 1))
        per_page = 20
        offset = (page - 1) * per_page
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Build query
                query = """
                    SELECT 
                        r.*,
                        u.full_name as user_name,
                        u.profile_pic as user_profile_pic,
                        o.order_id,
                        COALESCE(s.name, m.name) as item_name,
                        COALESCE(s.photo, m.photo) as item_photo
                    FROM reviews r
                    JOIN users u ON r.user_id = u.id
                    JOIN orders o ON r.order_id = o.order_id
                    LEFT JOIN services s ON r.item_type = 'service' AND r.item_id = s.id
                    LEFT JOIN menu m ON r.item_type = 'menu' AND r.item_id = m.id
                """
                
                params = []
                
                if approved != 'all':
                    query += " WHERE r.is_approved = %s"
                    params.append(approved == 'yes')
                
                query += " ORDER BY r.created_at DESC LIMIT %s OFFSET %s"
                params.extend([per_page, offset])
                
                cur.execute(query, params)
                reviews = cur.fetchall()
                
                # Count total reviews
                count_query = "SELECT COUNT(*) as total FROM reviews"
                count_params = []
                
                if approved != 'all':
                    count_query += " WHERE is_approved = %s"
                    count_params.append(approved == 'yes')
                
                cur.execute(count_query, count_params)
                total_reviews = cur.fetchone()['total']
                total_pages = (total_reviews + per_page - 1) // per_page
                
                # Format dates
                for review in reviews:
                    review['created_at_formatted'] = format_ist_datetime(review['created_at'])
        
        return render_template('reviews/list.html',
                           reviews=reviews,
                           approved=approved,
                           page=page,
                           total_pages=total_pages,
                           total_reviews=total_reviews)
        
    except Exception as e:
        logger.error(f"Reviews list error: {e}")
        flash(f'Error loading reviews: {str(e)}', 'error')
        return render_template('reviews/list.html',
                           reviews=[],
                           approved='all',
                           page=1,
                           total_pages=0,
                           total_reviews=0)

@app.route('/dashboard/reviews/<int:review_id>/toggle-approval', methods=['POST'])
@admin_login_required
def toggle_review_approval(review_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get current approval status
                cur.execute("SELECT is_approved FROM reviews WHERE review_id = %s", (review_id,))
                review = cur.fetchone()
                
                if not review:
                    return jsonify({'success': False, 'message': 'Review not found'})
                
                new_status = not review['is_approved']
                
                # Update approval status
                cur.execute("""
                    UPDATE reviews SET is_approved = %s WHERE review_id = %s
                """, (new_status, review_id))
                
                conn.commit()
                
                action = "approved" if new_status else "unapproved"
                logger.info(f"Review #{review_id} {action} by admin {session.get('username')}")
                
                return jsonify({
                    'success': True,
                    'message': f'Review {action} successfully',
                    'is_approved': new_status
                })
                
    except Exception as e:
        logger.error(f"Toggle review approval error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Notifications
@app.route('/dashboard/notifications')
@admin_login_required
def admin_notifications():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get recent notifications for admin
                cur.execute("""
                    SELECT 
                        n.*,
                        u.full_name as user_name,
                        u.phone as user_phone
                    FROM notifications n
                    JOIN users u ON n.user_id = u.id
                    ORDER BY n.created_at DESC
                    LIMIT 50
                """)
                
                notifications = cur.fetchall()
                
                # Format dates
                for notification in notifications:
                    notification['created_at_formatted'] = format_ist_datetime(notification['created_at'])
                    if notification['read_at']:
                        notification['read_at_formatted'] = format_ist_datetime(notification['read_at'])
        
        return render_template('notifications/list.html', notifications=notifications)
        
    except Exception as e:
        logger.error(f"Notifications error: {e}")
        flash(f'Error loading notifications: {str(e)}', 'error')
        return render_template('notifications/list.html', notifications=[])

# Admin profile
@app.route('/dashboard/profile', methods=['GET', 'POST'])
@admin_login_required
def admin_profile():
    if request.method == 'POST':
        try:
            full_name = request.form.get('full_name', '').strip()
            email = request.form.get('email', '').strip()
            current_password = request.form.get('current_password', '').strip()
            new_password = request.form.get('new_password', '').strip()
            confirm_password = request.form.get('confirm_password', '').strip()
            
            errors = []
            
            if not full_name:
                errors.append('Full name is required')
            if not email or '@' not in email:
                errors.append('Valid email is required')
            
            if new_password:
                if not current_password:
                    errors.append('Current password is required to set new password')
                elif new_password != confirm_password:
                    errors.append('New passwords do not match')
                elif len(new_password) < 6:
                    errors.append('New password must be at least 6 characters')
            
            if errors:
                for error in errors:
                    flash(error, 'error')
                return redirect(url_for('admin_profile'))
            
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Verify current password if changing password
                    if new_password:
                        cur.execute(
                            "SELECT password FROM admin_users WHERE admin_id = %s",
                            (session['admin_id'],)
                        )
                        admin = cur.fetchone()
                        
                        if not admin or not check_password_hash(admin['password'], current_password):
                            flash('Current password is incorrect', 'error')
                            return redirect(url_for('admin_profile'))
                    
                    # Check if email is already used by another admin
                    cur.execute(
                        "SELECT admin_id FROM admin_users WHERE email = %s AND admin_id != %s",
                        (email, session['admin_id'])
                    )
                    if cur.fetchone():
                        flash('Email already registered to another admin', 'error')
                        return redirect(url_for('admin_profile'))
                    
                    # Update admin profile
                    update_fields = ["full_name = %s", "email = %s"]
                    params = [full_name, email]
                    
                    if new_password:
                        hashed_password = generate_password_hash(new_password)
                        update_fields.append("password = %s")
                        params.append(hashed_password)
                    
                    params.append(session['admin_id'])
                    
                    update_query = f"""
                        UPDATE admin_users 
                        SET {', '.join(update_fields)}
                        WHERE admin_id = %s
                    """
                    
                    cur.execute(update_query, params)
                    conn.commit()
                    
                    # Update session
                    session['full_name'] = full_name
                    session['email'] = email
                    
                    flash('Profile updated successfully!', 'success')
                    logger.info(f"Admin {session.get('username')} updated their profile")
                    return redirect(url_for('admin_profile'))
                    
        except Exception as e:
            logger.error(f"Admin profile update error: {e}")
            flash(f'Error updating profile: {str(e)}', 'error')
            return redirect(url_for('admin_profile'))
    
    return render_template('admin/profile.html')

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

# Context processor for template variables
@app.context_processor
def inject_context():
    return {
        'ist_now': ist_now,
        'format_ist_datetime': format_ist_datetime,
        'admin_name': session.get('full_name', 'Admin'),
        'admin_role': session.get('role', 'admin')
    }

# Health check endpoint
@app.route('/health')
def health_check():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        return jsonify({
            'status': 'healthy',
            'service': 'BiteMeBuddy Admin Dashboard',
            'timestamp': ist_now().isoformat(),
            'timezone': 'Asia/Kolkata'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': ist_now().isoformat()
        }), 500

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5001)
