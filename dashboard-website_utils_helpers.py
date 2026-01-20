# dashboard-website/utils/helpers.py
import os
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
import pytz
import cloudinary
import cloudinary.api

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

def generate_google_maps_link(latitude, longitude):
    """Generate Google Maps link from latitude and longitude"""
    if latitude and longitude:
        return f"https://www.google.com/maps?q={latitude},{longitude}"
    return None

def format_currency(amount):
    """Format amount as Indian Rupees"""
    if amount is None:
        return "₹0.00"
    try:
        return f"₹{float(amount):,.2f}"
    except:
        return f"₹0.00"

def format_phone_number(phone):
    """Format phone number for display"""
    if not phone:
        return ""
    phone = str(phone).strip()
    if phone.startswith('+91'):
        return phone
    elif phone.startswith('91') and len(phone) == 12:
        return '+' + phone
    elif len(phone) == 10:
        return '+91 ' + phone[:5] + ' ' + phone[5:]
    else:
        return phone

def validate_email(email):
    """Validate email format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone number"""
    import re
    pattern = r'^(\+91[\-\s]?)?[0]?(91)?[789]\d{9}$'
    return re.match(pattern, str(phone)) is not None

def calculate_discount_percentage(original_price, final_price):
    """Calculate discount percentage"""
    if not original_price or not final_price or original_price <= 0:
        return 0
    discount = ((original_price - final_price) / original_price) * 100
    return round(discount, 1)

def calculate_age(date_of_birth):
    """Calculate age from date of birth"""
    if not date_of_birth:
        return None
    today = ist_now().date()
    return today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))

def get_time_ago(dt):
    """Get human readable time difference"""
    if not dt:
        return "Unknown"
    
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    
    now = ist_now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 2592000:  # 30 days
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif seconds < 31536000:  # 365 days
        months = int(seconds / 2592000)
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = int(seconds / 31536000)
        return f"{years} year{'s' if years != 1 else ''} ago"

def truncate_text(text, length=100):
    """Truncate text to specified length"""
    if not text:
        return ""
    if len(text) <= length:
        return text
    return text[:length] + "..."

def generate_order_number(order_id):
    """Generate human readable order number"""
    return f"BMB{order_id:06d}"

def parse_location_string(location):
    """Parse location string into components"""
    if not location:
        return {}
    
    # Check if location contains latitude/longitude
    if '|' in location:
        parts = location.split('|')
        if len(parts) >= 4:
            return {
                'address': parts[0].strip(),
                'latitude': float(parts[1].strip()) if parts[1].strip() else None,
                'longitude': float(parts[2].strip()) if parts[2].strip() else None,
                'map_link': parts[3].strip() if len(parts) > 3 else None
            }
    
    return {'address': location.strip()}

def upload_to_cloudinary(file, folder, public_id=None, transformation=None):
    """Upload file to Cloudinary"""
    try:
        if not file or not file.filename:
            return None
        
        upload_kwargs = {
            'folder': folder,
            'overwrite': True,
            'resource_type': 'auto'
        }
        
        if public_id:
            upload_kwargs['public_id'] = public_id
        
        if transformation:
            upload_kwargs['transformation'] = transformation
        
        result = cloudinary.uploader.upload(file, **upload_kwargs)
        
        return {
            'url': result['secure_url'],
            'public_id': result['public_id'],
            'format': result['format'],
            'width': result['width'],
            'height': result['height']
        }
    except Exception as e:
        logger.error(f"Cloudinary upload error: {e}")
        return None

def delete_from_cloudinary(public_id):
    """Delete file from Cloudinary"""
    try:
        if not public_id:
            return False
        
        result = cloudinary.uploader.destroy(public_id)
        return result.get('result') == 'ok'
    except Exception as e:
        logger.error(f"Cloudinary delete error: {e}")
        return False

def get_cloudinary_resources(folder, max_results=100):
    """Get resources from Cloudinary folder"""
    try:
        result = cloudinary.api.resources(
            type="upload",
            prefix=folder,
            max_results=max_results
        )
        return result.get('resources', [])
    except Exception as e:
        logger.error(f"Cloudinary resources error: {e}")
        return []

def calculate_order_stats(orders):
    """Calculate statistics from orders list"""
    if not orders:
        return {
            'total_orders': 0,
            'total_revenue': 0,
            'avg_order_value': 0,
            'pending_orders': 0,
            'delivered_orders': 0
        }
    
    total_orders = len(orders)
    total_revenue = sum(float(order.get('total_amount', 0)) for order in orders)
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    pending_orders = sum(1 for order in orders if order.get('status') == 'pending')
    delivered_orders = sum(1 for order in orders if order.get('status') == 'delivered')
    
    return {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'avg_order_value': avg_order_value,
        'pending_orders': pending_orders,
        'delivered_orders': delivered_orders
    }

def get_date_ranges(period='today'):
    """Get date ranges for different periods"""
    now = ist_now()
    
    if period == 'today':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
    elif period == 'yesterday':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        end = start + timedelta(days=1)
    elif period == 'week':
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=7)
    elif period == 'month':
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            end = now.replace(year=now.year+1, month=1, day=1)
        else:
            end = now.replace(month=now.month+1, day=1)
    elif period == 'year':
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(year=now.year+1, month=1, day=1)
    else:
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
    
    return {
        'start': start,
        'end': end,
        'start_utc': start.astimezone(pytz.utc),
        'end_utc': end.astimezone(pytz.utc)
    }

def generate_pagination(page, total_pages, url_base, params=None):
    """Generate pagination data"""
    if params is None:
        params = {}
    
    pagination = {
        'current_page': page,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_url': None,
        'next_url': None
    }
    
    if pagination['has_prev']:
        prev_params = params.copy()
        prev_params['page'] = page - 1
        pagination['prev_url'] = f"{url_base}?{'&'.join(f'{k}={v}' for k, v in prev_params.items())}"
    
    if pagination['has_next']:
        next_params = params.copy()
        next_params['page'] = page + 1
        pagination['next_url'] = f"{url_base}?{'&'.join(f'{k}={v}' for k, v in next_params.items())}"
    
    # Calculate page numbers to display
    pages = []
    if total_pages <= 7:
        pages = list(range(1, total_pages + 1))
    else:
        if page <= 4:
            pages = list(range(1, 6)) + ['...', total_pages]
        elif page >= total_pages - 3:
            pages = [1, '...'] + list(range(total_pages - 4, total_pages + 1))
        else:
            pages = [1, '...'] + list(range(page - 2, page + 3)) + ['...', total_pages]
    
    pagination['pages'] = pages
    
    return pagination

def format_bytes(size_bytes):
    """Format bytes to human readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.1f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.1f} GB"

def sanitize_input(text):
    """Sanitize user input"""
    if not text:
        return ""
    
    import html
    text = html.escape(text)
    
    # Remove potentially dangerous characters
    dangerous = ['<script>', '</script>', 'javascript:', 'onclick', 'onload', 'onerror']
    for d in dangerous:
        text = text.replace(d, '')
    
    return text.strip()

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    
    if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?/' for c in password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is strong"