# dashboard-website/utils/validators.py
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

def validate_email(email):
    """Validate email address format"""
    if not email:
        return False, "Email is required"
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Invalid email format"
    
    return True, "Email is valid"

def validate_phone(phone):
    """Validate phone number format"""
    if not phone:
        return False, "Phone number is required"
    
    # Remove any non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', str(phone))
    
    # Check for valid Indian phone numbers
    pattern = r'^(\+91|91|0)?[6789]\d{9}$'
    if not re.match(pattern, cleaned):
        return False, "Invalid phone number format"
    
    return True, "Phone number is valid"

def validate_name(name):
    """Validate person name"""
    if not name or not name.strip():
        return False, "Name is required"
    
    if len(name.strip()) < 2:
        return False, "Name must be at least 2 characters long"
    
    if len(name.strip()) > 100:
        return False, "Name must be less than 100 characters"
    
    # Allow only letters, spaces, and common name characters
    pattern = r'^[a-zA-Z\s\.\'-]+$'
    if not re.match(pattern, name):
        return False, "Name contains invalid characters"
    
    return True, "Name is valid"

def validate_password(password):
    """Validate password strength"""
    if not password:
        return False, "Password is required"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>/?]', password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is strong"

def validate_amount(amount):
    """Validate monetary amount"""
    if amount is None:
        return False, "Amount is required"
    
    try:
        amount_decimal = Decimal(str(amount))
        if amount_decimal < 0:
            return False, "Amount cannot be negative"
        
        if amount_decimal > Decimal('10000000'):  # 10 million limit
            return False, "Amount is too large"
        
        return True, "Amount is valid"
    except InvalidOperation:
        return False, "Invalid amount format"

def validate_quantity(quantity):
    """Validate item quantity"""
    if quantity is None:
        return False, "Quantity is required"
    
    try:
        qty = int(quantity)
        if qty <= 0:
            return False, "Quantity must be greater than 0"
        
        if qty > 1000:  # Reasonable limit
            return False, "Quantity is too large"
        
        return True, "Quantity is valid"
    except ValueError:
        return False, "Invalid quantity format"

def validate_date(date_str, date_format='%Y-%m-%d'):
    """Validate date string"""
    if not date_str:
        return False, "Date is required"
    
    try:
        datetime.strptime(date_str, date_format)
        return True, "Date is valid"
    except ValueError:
        return False, f"Invalid date format. Expected: {date_format}"

def validate_pincode(pincode):
    """Validate Indian pincode"""
    if not pincode:
        return False, "Pincode is required"
    
    pattern = r'^[1-9][0-9]{5}$'
    if not re.match(pattern, str(pincode)):
        return False, "Invalid pincode format (6 digits required)"
    
    return True, "Pincode is valid"

def validate_address(address):
    """Validate address"""
    if not address or not address.strip():
        return False, "Address is required"
    
    if len(address.strip()) < 10:
        return False, "Address must be at least 10 characters long"
    
    if len(address.strip()) > 500:
        return False, "Address is too long (max 500 characters)"
    
    return True, "Address is valid"

def validate_coordinate(coord, coord_type='latitude'):
    """Validate latitude or longitude coordinate"""
    if coord is None:
        return False, f"{coord_type.title()} is required"
    
    try:
        coord_float = float(coord)
        
        if coord_type == 'latitude':
            if not -90 <= coord_float <= 90:
                return False, "Latitude must be between -90 and 90"
        else:  # longitude
            if not -180 <= coord_float <= 180:
                return False, "Longitude must be between -180 and 180"
        
        return True, f"{coord_type.title()} is valid"
    except ValueError:
        return False, f"Invalid {coord_type} format"

def validate_url(url):
    """Validate URL format"""
    if not url:
        return False, "URL is required"
    
    pattern = r'^https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?:/[-\w.%?=&]*)*$'
    if not re.match(pattern, url):
        return False, "Invalid URL format"
    
    return True, "URL is valid"

def validate_file_extension(filename, allowed_extensions=None):
    """Validate file extension"""
    if not filename:
        return False, "Filename is required"
    
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
    
    extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    if not extension:
        return False, "File must have an extension"
    
    if extension not in allowed_extensions:
        return False, f"File type not allowed. Allowed: {', '.join(allowed_extensions)}"
    
    return True, "File extension is valid"

def validate_file_size(file_size, max_size_mb=10):
    """Validate file size"""
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if file_size > max_size_bytes:
        return False, f"File size exceeds {max_size_mb}MB limit"
    
    return True, "File size is valid"

def validate_json(json_str):
    """Validate JSON string"""
    if not json_str:
        return False, "JSON is required"
    
    try:
        import json
        json.loads(json_str)
        return True, "JSON is valid"
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {str(e)}"

def validate_range(value, min_val, max_val):
    """Validate value is within range"""
    if value is None:
        return False, "Value is required"
    
    try:
        num = float(value)
        if not min_val <= num <= max_val:
            return False, f"Value must be between {min_val} and {max_val}"
        
        return True, "Value is within range"
    except ValueError:
        return False, "Invalid numeric value"

def validate_rating(rating):
    """Validate rating (1-5)"""
    return validate_range(rating, 1, 5)

def validate_discount(discount):
    """Validate discount percentage"""
    return validate_range(discount, 0, 100)

def validate_status(status, allowed_statuses=None):
    """Validate status value"""
    if allowed_statuses is None:
        allowed_statuses = {'active', 'inactive', 'pending', 'approved', 'rejected'}
    
    if status not in allowed_statuses:
        return False, f"Invalid status. Allowed: {', '.join(allowed_statuses)}"
    
    return True, "Status is valid"

def validate_category(category, allowed_categories=None):
    """Validate category"""
    if not category:
        return False, "Category is required"
    
    if allowed_categories and category not in allowed_categories:
        return False, f"Invalid category. Allowed: {', '.join(allowed_categories)}"
    
    return True, "Category is valid"

def validate_description(description, min_length=10, max_length=2000):
    """Validate description"""
    if not description:
        return False, "Description is required"
    
    if len(description) < min_length:
        return False, f"Description must be at least {min_length} characters long"
    
    if len(description) > max_length:
        return False, f"Description must be less than {max_length} characters"
    
    return True, "Description is valid"

def validate_order_status(status):
    """Validate order status"""
    allowed_statuses = {'pending', 'confirmed', 'processing', 'out_for_delivery', 'delivered', 'cancelled'}
    return validate_status(status, allowed_statuses)

def validate_payment_mode(mode):
    """Validate payment mode"""
    allowed_modes = {'cod', 'online', 'card', 'wallet', 'upi'}
    return validate_status(mode, allowed_modes)

def validate_payment_status(status):
    """Validate payment status"""
    allowed_statuses = {'pending', 'completed', 'failed', 'refunded', 'cancelled'}
    return validate_status(status, allowed_statuses)

def validate_item_type(item_type):
    """Validate item type"""
    allowed_types = {'service', 'menu'}
    return validate_status(item_type, allowed_types)

def validate_notification_type(notification_type):
    """Validate notification type"""
    allowed_types = {'order_update', 'payment', 'system', 'promotion', 'alert'}
    return validate_status(notification_type, allowed_types)

def validate_user_role(role):
    """Validate user role"""
    allowed_roles = {'admin', 'user', 'manager', 'superadmin'}
    return validate_status(role, allowed_roles)

def validate_service_category(category):
    """Validate service category"""
    if not category:
        return True, "Category is optional"
    
    if len(category) > 50:
        return False, "Category must be less than 50 characters"
    
    return True, "Category is valid"

def validate_menu_category(category):
    """Validate menu category"""
    if not category:
        return True, "Category is optional"
    
    if len(category) > 50:
        return False, "Category must be less than 50 characters"
    
    return True, "Category is valid"

def validate_position(position):
    """Validate position/number"""
    if position is None:
        return True, "Position is optional"
    
    try:
        pos = int(position)
        if pos < 0:
            return False, "Position cannot be negative"
        
        if pos > 1000:
            return False, "Position is too large"
        
        return True, "Position is valid"
    except ValueError:
        return False, "Invalid position format"
