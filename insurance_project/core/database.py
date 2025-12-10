"""
Database connection and query handler using PyMySQL
"""
import pymysql
import logging
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'password',
    'database': 'insurance_db',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
}

class DatabaseConnection:
    """Database connection handler using PyMySQL"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or DB_CONFIG
        self.connection = None
        
    def connect(self) -> None:
        """Establish database connection"""
        try:
            self.connection = pymysql.connect(**self.config)
            logger.info("Database connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def disconnect(self) -> None:
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Database connection closed")
    
    @contextmanager
    def cursor(self):
        """Context manager for database cursor"""
        if not self.connection:
            self.connect()
        try:
            cursor = self.connection.cursor()
            yield cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            cursor.close()
    
    def execute_query(self, sql: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """Execute SELECT query and return results"""
        try:
            with self.cursor() as cursor:
                cursor.execute(sql, params)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def execute_update(self, sql: str, params: Optional[Tuple] = None) -> int:
        """Execute INSERT, UPDATE, DELETE query and return affected rows"""
        try:
            with self.cursor() as cursor:
                affected_rows = cursor.execute(sql, params)
                return affected_rows
        except Exception as e:
            logger.error(f"Update execution failed: {e}")
            raise
    
    def execute_insert(self, sql: str, params: Optional[Tuple] = None) -> int:
        """Execute INSERT query and return last inserted ID"""
        try:
            with self.cursor() as cursor:
                cursor.execute(sql, params)
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Insert execution failed: {e}")
            raise
    
    def execute_batch(self, sql: str, params_list: List[Tuple]) -> int:
        """Execute multiple queries in a batch"""
        try:
            with self.cursor() as cursor:
                affected_rows = cursor.executemany(sql, params_list)
                return affected_rows
        except Exception as e:
            logger.error(f"Batch execution failed: {e}")
            raise

# Create a singleton database instance
db = DatabaseConnection()

# SQL queries for form_data table
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS form_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(100) NOT NULL,
    task_name VARCHAR(100) NOT NULL,
    company VARCHAR(100) NOT NULL,
    scene VARCHAR(100) NOT NULL,
    progress VARCHAR(100) NOT NULL,
    status VARCHAR(100) NOT NULL,
    llm_content LONGTEXT,
    update_content LONGTEXT,
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_task_id (task_id),
    INDEX idx_task_name (task_name),
    INDEX idx_company (company),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

# Form data queries
SELECT_FORM_DATA = """
SELECT id, task_id, task_name, company, scene, progress, status, 
       llm_content, update_content, create_time
FROM form_data
WHERE (%(task_name)s IS NULL OR task_name LIKE %(task_name_pattern)s)
  AND (%(company)s IS NULL OR company = %(company)s)
ORDER BY create_time DESC
LIMIT %(limit)s OFFSET %(offset)s
"""

COUNT_FORM_DATA = """
SELECT COUNT(*) as total
FROM form_data
WHERE (%(task_name)s IS NULL OR task_name LIKE %(task_name_pattern)s)
  AND (%(company)s IS NULL OR company = %(company)s)
"""

SELECT_FORM_BY_TASK_ID = """
SELECT id, task_id, task_name, company, scene, progress, status, 
       llm_content, update_content, create_time
FROM form_data
WHERE task_id = %(task_id)s
"""

INSERT_FORM_DATA = """
INSERT INTO form_data (task_id, task_name, company, scene, progress, status, llm_content)
VALUES (%(task_id)s, %(task_name)s, %(company)s, %(scene)s, %(progress)s, %(status)s, %(llm_content)s)
"""

UPDATE_FORM_STATUS = """
UPDATE form_data 
SET task_name = %(task_name)s,
    company = %(company)s,
    scene = %(scene)s,
    progress = %(progress)s,
    status = %(status)s,
    llm_content = %(llm_content)s
WHERE task_id = %(task_id)s
"""

UPDATE_FORM_CONTENT = """
UPDATE form_data 
SET update_content = %(update_content)s
WHERE task_id = %(task_id)s
"""

DELETE_FORM_BY_TASK_ID = """
DELETE FROM form_data
WHERE task_id = %(task_id)s
"""

DELETE_FORM_BATCH = """
DELETE FROM form_data
WHERE task_id IN %(task_ids)s
"""

def init_database():
    """Initialize database and create tables"""
    try:
        db.execute_query(CREATE_TABLE_SQL)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise