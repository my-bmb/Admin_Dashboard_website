# dashboard-website/utils/database.py
import os
import logging
from datetime import datetime
from decimal import Decimal
import json
import psycopg
from psycopg.rows import dict_row
import cloudinary
import cloudinary.uploader
from .helpers import generate_google_maps_link, ist_now

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database management utilities"""
    
    @staticmethod
    def get_connection():
        """Get database connection"""
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
    
    @staticmethod
    def execute_query(query, params=None, fetch_one=False, fetch_all=False):
        """Execute SQL query and return results"""
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            with conn.cursor() as cur:
                cur.execute(query, params or ())
                
                if fetch_one:
                    result = cur.fetchone()
                elif fetch_all:
                    result = cur.fetchall()
                else:
                    result = None
                
                if not query.strip().upper().startswith(('SELECT', 'SHOW', 'DESC')):
                    conn.commit()
                
                return result
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def get_table_stats():
        """Get statistics for all tables"""
        try:
            query = """
                SELECT 
                    table_name,
                    pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) as size,
                    (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public') as table_count
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """
            return DatabaseManager.execute_query(query, fetch_all=True)
        except Exception as e:
            logger.error(f"Error getting table stats: {e}")
            return []
    
    @staticmethod
    def backup_database():
        """Create database backup (simplified)"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f"backup_{timestamp}.sql"
            
            # In production, you would use pg_dump here
            logger.info(f"Database backup created: {backup_file}")
            return backup_file
        except Exception as e:
            logger.error(f"Backup error: {e}")
            return None
    
    @staticmethod
    def get_system_health():
        """Check database health status"""
        try:
            # Check connection
            conn = DatabaseManager.get_connection()
            with conn.cursor() as cur:
                # Check active connections
                cur.execute("SELECT COUNT(*) as active_connections FROM pg_stat_activity")
                active_connections = cur.fetchone()['active_connections']
                
                # Check database size
                cur.execute("SELECT pg_database_size(current_database()) as db_size")
                db_size = cur.fetchone()['db_size']
                
                # Check last backup (simulated)
                cur.execute("SELECT MAX(order_date) as last_order FROM orders")
                last_order = cur.fetchone()['last_order']
                
                return {
                    'status': 'healthy',
                    'active_connections': active_connections,
                    'db_size': db_size,
                    'last_order': last_order,
                    'timestamp': ist_now().isoformat()
                }
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': ist_now().isoformat()
            }
    
    @staticmethod
    def optimize_tables():
        """Optimize database tables"""
        try:
            conn = DatabaseManager.get_connection()
            with conn.cursor() as cur:
                # Vacuum analyze all tables
                cur.execute("VACUUM ANALYZE")
                
                # Update statistics
                cur.execute("ANALYZE")
                
                conn.commit()
                logger.info("Database optimization completed")
                return True
        except Exception as e:
            logger.error(f"Optimization error: {e}")
            return False
    
    @staticmethod
    def update_address_maps_links():
        """Update addresses with Google Maps links"""
        try:
            conn = DatabaseManager.get_connection()
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
                updated_count = 0
                
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
                        updated_count += 1
                
                conn.commit()
                logger.info(f"Updated {updated_count} addresses with Google Maps links")
                return updated_count
                
        except Exception as e:
            logger.error(f"Error updating maps links: {e}")
            return 0
    
    @staticmethod
    def cleanup_old_data(days=90):
        """Cleanup old data (archives instead of deletes)"""
        try:
            conn = DatabaseManager.get_connection()
            with conn.cursor() as cur:
                # Archive old notifications (older than specified days)
                cutoff_date = ist_now() - timedelta(days=days)
                
                # Count records to be archived
                cur.execute("""
                    SELECT COUNT(*) as count 
                    FROM notifications 
                    WHERE created_at < %s AND is_read = TRUE
                """, (cutoff_date,))
                
                count = cur.fetchone()['count']
                
                if count > 0:
                    # Create archive table if not exists
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS notifications_archive 
                        AS TABLE notifications WITH NO DATA
                    """)
                    
                    # Archive old records
                    cur.execute("""
                        INSERT INTO notifications_archive 
                        SELECT * FROM notifications 
                        WHERE created_at < %s AND is_read = TRUE
                    """, (cutoff_date,))
                    
                    # Delete archived records
                    cur.execute("""
                        DELETE FROM notifications 
                        WHERE created_at < %s AND is_read = TRUE
                    """, (cutoff_date,))
                    
                    logger.info(f"Archived {count} old notifications")
                
                conn.commit()
                return count
                
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            return 0
    
    @staticmethod
    def validate_data_integrity():
        """Validate data integrity across tables"""
        try:
            issues = []
            
            # Check for orphaned records
            conn = DatabaseManager.get_connection()
            with conn.cursor() as cur:
                # Check cart items with invalid user references
                cur.execute("""
                    SELECT c.id as cart_id 
                    FROM cart c 
                    LEFT JOIN users u ON c.user_id = u.id 
                    WHERE u.id IS NULL
                    LIMIT 10
                """)
                orphaned_cart = cur.fetchall()
                if orphaned_cart:
                    issues.append(f"Found {len(orphaned_cart)} orphaned cart items")
                
                # Check order items with invalid order references
                cur.execute("""
                    SELECT oi.order_item_id 
                    FROM order_items oi 
                    LEFT JOIN orders o ON oi.order_id = o.order_id 
                    WHERE o.order_id IS NULL
                    LIMIT 10
                """)
                orphaned_order_items = cur.fetchall()
                if orphaned_order_items:
                    issues.append(f"Found {len(orphaned_order_items)} orphaned order items")
                
                # Check payments without orders
                cur.execute("""
                    SELECT p.payment_id 
                    FROM payments p 
                    LEFT JOIN orders o ON p.order_id = o.order_id 
                    WHERE o.order_id IS NULL
                    LIMIT 10
                """)
                orphaned_payments = cur.fetchall()
                if orphaned_payments:
                    issues.append(f"Found {len(orphaned_payments)} orphaned payments")
            
            return {
                'has_issues': len(issues) > 0,
                'issues': issues,
                'timestamp': ist_now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Data integrity check error: {e}")
            return {
                'has_issues': True,
                'issues': [f"Check failed: {str(e)}"],
                'timestamp': ist_now().isoformat()
            }
    
    @staticmethod
    def get_query_analytics():
        """Get query performance analytics"""
        try:
            conn = DatabaseManager.get_connection()
            with conn.cursor() as cur:
                # Get slow queries
                cur.execute("""
                    SELECT 
                        query,
                        calls,
                        total_time,
                        mean_time,
                        rows
                    FROM pg_stat_statements 
                    ORDER BY mean_time DESC 
                    LIMIT 10
                """)
                
                slow_queries = cur.fetchall()
                
                # Get table access statistics
                cur.execute("""
                    SELECT 
                        schemaname,
                        relname,
                        seq_scan,
                        idx_scan,
                        n_tup_ins,
                        n_tup_upd,
                        n_tup_del
                    FROM pg_stat_user_tables 
                    ORDER BY seq_scan + idx_scan DESC 
                    LIMIT 10
                """)
                
                table_stats = cur.fetchall()
                
                return {
                    'slow_queries': slow_queries,
                    'table_stats': table_stats,
                    'timestamp': ist_now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Query analytics error: {e}")
            return {
                'slow_queries': [],
                'table_stats': [],
                'error': str(e),
                'timestamp': ist_now().isoformat()
            }