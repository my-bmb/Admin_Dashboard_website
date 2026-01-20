# dashboard-website/config/constants.py
"""Application constants"""

# Order Statuses
ORDER_STATUS = {
    'PENDING': 'pending',
    'CONFIRMED': 'confirmed',
    'PROCESSING': 'processing',
    'OUT_FOR_DELIVERY': 'out_for_delivery',
    'DELIVERED': 'delivered',
    'CANCELLED': 'cancelled'
}

ORDER_STATUS_DISPLAY = {
    'pending': 'Pending',
    'confirmed': 'Confirmed',
    'processing': 'Processing',
    'out_for_delivery': 'Out for Delivery',
    'delivered': 'Delivered',
    'cancelled': 'Cancelled'
}

ORDER_STATUS_COLORS = {
    'pending': 'primary',
    'confirmed': 'info',
    'processing': 'warning',
    'out_for_delivery': 'secondary',
    'delivered': 'success',
    'cancelled': 'danger'
}

# Payment Statuses
PAYMENT_STATUS = {
    'PENDING': 'pending',
    'COMPLETED': 'completed',
    'FAILED': 'failed',
    'REFUNDED': 'refunded',
    'CANCELLED': 'cancelled'
}

PAYMENT_STATUS_DISPLAY = {
    'pending': 'Pending',
    'completed': 'Completed',
    'failed': 'Failed',
    'refunded': 'Refunded',
    'cancelled': 'Cancelled'
}

PAYMENT_STATUS_COLORS = {
    'pending': 'warning',
    'completed': 'success',
    'failed': 'danger',
    'refunded': 'info',
    'cancelled': 'secondary'
}

# Payment Modes
PAYMENT_MODES = {
    'COD': 'cod',
    'ONLINE': 'online',
    'CARD': 'card',
    'WALLET': 'wallet',
    'UPI': 'upi'
}

PAYMENT_MODES_DISPLAY = {
    'cod': 'Cash on Delivery',
    'online': 'Online Payment',
    'card': 'Credit/Debit Card',
    'wallet': 'Digital Wallet',
    'upi': 'UPI'
}

# Item Types
ITEM_TYPES = {
    'SERVICE': 'service',
    'MENU': 'menu'
}

ITEM_TYPES_DISPLAY = {
    'service': 'Service',
    'menu': 'Menu Item'
}

# User Status
USER_STATUS = {
    'ACTIVE': 'active',
    'INACTIVE': 'inactive',
    'SUSPENDED': 'suspended'
}

USER_STATUS_DISPLAY = {
    'active': 'Active',
    'inactive': 'Inactive',
    'suspended': 'Suspended'
}

USER_STATUS_COLORS = {
    'active': 'success',
    'inactive': 'secondary',
    'suspended': 'danger'
}

# Admin Roles
ADMIN_ROLES = {
    'SUPERADMIN': 'superadmin',
    'ADMIN': 'admin',
    'MANAGER': 'manager',
    'VIEWER': 'viewer'
}

ADMIN_ROLES_DISPLAY = {
    'superadmin': 'Super Admin',
    'admin': 'Admin',
    'manager': 'Manager',
    'viewer': 'Viewer'
}

# Notification Types
NOTIFICATION_TYPES = {
    'ORDER_UPDATE': 'order_update',
    'PAYMENT': 'payment',
    'SYSTEM': 'system',
    'PROMOTION': 'promotion',
    'ALERT': 'alert'
}

NOTIFICATION_TYPES_DISPLAY = {
    'order_update': 'Order Update',
    'payment': 'Payment',
    'system': 'System',
    'promotion': 'Promotion',
    'alert': 'Alert'
}

# Service/Menu Status
ITEM_STATUS = {
    'ACTIVE': 'active',
    'INACTIVE': 'inactive',
    'OUT_OF_STOCK': 'out_of_stock'
}

ITEM_STATUS_DISPLAY = {
    'active': 'Active',
    'inactive': 'Inactive',
    'out_of_stock': 'Out of Stock'
}

ITEM_STATUS_COLORS = {
    'active': 'success',
    'inactive': 'secondary',
    'out_of_stock': 'warning'
}

# Review Status
REVIEW_STATUS = {
    'PENDING': 'pending',
    'APPROVED': 'approved',
    'REJECTED': 'rejected'
}

REVIEW_STATUS_DISPLAY = {
    'pending': 'Pending Approval',
    'approved': 'Approved',
    'rejected': 'Rejected'
}

REVIEW_STATUS_COLORS = {
    'pending': 'warning',
    'approved': 'success',
    'rejected': 'danger'
}

# Address Types
ADDRESS_TYPES = {
    'HOME': 'home',
    'WORK': 'work',
    'OTHER': 'other'
}

ADDRESS_TYPES_DISPLAY = {
    'home': 'Home',
    'work': 'Work',
    'other': 'Other'
}

# Cloudinary Folders
CLOUDINARY_FOLDERS = {
    'PROFILE_PICS': 'profile_pics',
    'SERVICES': 'services',
    'MENU_ITEMS': 'menu_items',
    'ORDER_ITEMS': 'order_items',
    'DOCUMENTS': 'documents'
}

# Date/Time Formats
DATE_FORMATS = {
    'DISPLAY': '%d %b %Y',
    'DISPLAY_FULL': '%d %b %Y, %I:%M %p',
    'DATABASE': '%Y-%m-%d %H:%M:%S',
    'FILENAME': '%Y%m%d_%H%M%S'
}

# Currency
CURRENCY = {
    'SYMBOL': '₹',
    'CODE': 'INR',
    'NAME': 'Indian Rupee'
}

# Pagination
PAGINATION = {
    'DEFAULT_PER_PAGE': 20,
    'MAX_PER_PAGE': 100,
    'PAGE_RANGE': 5
}

# File Upload
FILE_UPLOAD = {
    'MAX_SIZE_MB': 10,
    'ALLOWED_EXTENSIONS': {
        'images': {'png', 'jpg', 'jpeg', 'gif', 'webp'},
        'documents': {'pdf', 'doc', 'docx', 'txt'},
        'all': {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'doc', 'docx', 'txt'}
    }
}

# Validation
VALIDATION = {
    'PASSWORD_MIN_LENGTH': 8,
    'NAME_MAX_LENGTH': 100,
    'EMAIL_MAX_LENGTH': 100,
    'PHONE_MAX_LENGTH': 15,
    'ADDRESS_MAX_LENGTH': 500,
    'DESCRIPTION_MAX_LENGTH': 2000,
    'TITLE_MAX_LENGTH': 100
}

# Analytics
ANALYTICS_PERIODS = {
    'TODAY': 'today',
    'YESTERDAY': 'yesterday',
    'WEEK': 'week',
    'MONTH': 'month',
    'YEAR': 'year',
    'CUSTOM': 'custom'
}

# Chart Colors
CHART_COLORS = {
    'PRIMARY': '#667eea',
    'SECONDARY': '#764ba2',
    'SUCCESS': '#48bb78',
    'DANGER': '#f56565',
    'WARNING': '#ed8936',
    'INFO': '#38b2ac',
    'LIGHT': '#e2e8f0',
    'DARK': '#2d3748'
}

CHART_COLOR_PALETTE = [
    '#667eea', '#764ba2', '#48bb78', '#f56565', '#ed8936',
    '#38b2ac', '#ecc94b', '#9f7aea', '#ed64a6', '#4299e1'
]

# API Response Codes
API_RESPONSE = {
    'SUCCESS': 'success',
    'ERROR': 'error',
    'VALIDATION_ERROR': 'validation_error',
    'AUTH_ERROR': 'auth_error',
    'NOT_FOUND': 'not_found',
    'SERVER_ERROR': 'server_error'
}

# HTTP Status Codes
HTTP_STATUS = {
    'OK': 200,
    'CREATED': 201,
    'BAD_REQUEST': 400,
    'UNAUTHORIZED': 401,
    'FORBIDDEN': 403,
    'NOT_FOUND': 404,
    'METHOD_NOT_ALLOWED': 405,
    'CONFLICT': 409,
    'SERVER_ERROR': 500
}

# Error Messages
ERROR_MESSAGES = {
    'REQUIRED_FIELD': 'This field is required',
    'INVALID_EMAIL': 'Please enter a valid email address',
    'INVALID_PHONE': 'Please enter a valid phone number',
    'PASSWORD_MISMATCH': 'Passwords do not match',
    'INVALID_CREDENTIALS': 'Invalid username or password',
    'ACCESS_DENIED': 'You do not have permission to access this resource',
    'NOT_FOUND': 'The requested resource was not found',
    'SERVER_ERROR': 'An internal server error occurred',
    'VALIDATION_ERROR': 'Please check the form for errors'
}

# Success Messages
SUCCESS_MESSAGES = {
    'CREATED': 'Record created successfully',
    'UPDATED': 'Record updated successfully',
    'DELETED': 'Record deleted successfully',
    'LOGIN': 'Login successful',
    'LOGOUT': 'Logout successful',
    'PASSWORD_RESET': 'Password reset successful'
}

# Default Values
DEFAULTS = {
    'PROFILE_PIC': 'https://res.cloudinary.com/demo/image/upload/v1234567890/profile_pics/default-avatar.png',
    'SERVICE_PHOTO': 'https://res.cloudinary.com/demo/image/upload/v1633427556/sample_service.jpg',
    'MENU_PHOTO': 'https://res.cloudinary.com/demo/image/upload/v1633427556/sample_food.jpg',
    'PAGE_TITLE': 'BiteMeBuddy Admin Dashboard',
    'ITEMS_PER_PAGE': 20,
    'CACHE_TIMEOUT': 300
}
