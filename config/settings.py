# dashboard-website/config/settings.py
import os
from datetime import timedelta

class Config:
    """Base configuration"""
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'admin-dashboard-secret-key-change-me')
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Session
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Database
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    # Cloudinary
    CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')
    
    # Application
    TIMEZONE = 'Asia/Kolkata'
    APP_NAME = 'BiteMeBuddy Admin Dashboard'
    APP_VERSION = '1.0.0'
    
    # Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
    
    # Security
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_DIGITS = True
    PASSWORD_REQUIRE_SPECIAL = True
    
    # Pagination
    DEFAULT_ITEMS_PER_PAGE = 20
    MAX_ITEMS_PER_PAGE = 100
    
    # Analytics
    ENABLE_REALTIME_ANALYTICS = True
    ANALYTICS_REFRESH_INTERVAL = 60  # seconds
    
    # Notifications
    NOTIFICATION_RETENTION_DAYS = 90
    ENABLE_EMAIL_NOTIFICATIONS = False
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Backup
    ENABLE_AUTO_BACKUP = False
    BACKUP_RETENTION_DAYS = 7
    
    # Caching
    ENABLE_CACHING = True
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # API Rate Limiting
    ENABLE_RATE_LIMITING = True
    RATE_LIMIT_DEFAULT = "100 per minute"
    
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        """Get database URI"""
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL not configured")
        
        if self.DATABASE_URL.startswith('postgres://'):
            return self.DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        
        return self.DATABASE_URL
    
    @classmethod
    def init_app(cls, app):
        """Initialize application with config"""
        app.config.from_object(cls)

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    ENABLE_REALTIME_ANALYTICS = True
    LOG_LEVEL = 'DEBUG'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    DATABASE_URL = os.environ.get('TEST_DATABASE_URL', 'postgresql://localhost/bitemebuddy_test')
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    ENABLE_REALTIME_ANALYTICS = True
    LOG_LEVEL = 'WARNING'
    ENABLE_AUTO_BACKUP = True
    
    @classmethod
    def init_app(cls, app):
        """Production-specific initialization"""
        Config.init_app(app)
        
        # Email errors to administrators
        import logging
        from logging.handlers import SMTPHandler
        
        credentials = None
        secure = None
        
        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()
        
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.MAIL_DEFAULT_SENDER,
            toaddrs=[cls.ADMIN_EMAIL],
            subject=f'{cls.APP_NAME} Application Error',
            credentials=credentials,
            secure=secure
        )
        
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)

class StagingConfig(ProductionConfig):
    """Staging configuration"""
    DEBUG = True
    LOG_LEVEL = 'INFO'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'staging': StagingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    """Get configuration class by name"""
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')
    
    return config.get(config_name, config['default'])
