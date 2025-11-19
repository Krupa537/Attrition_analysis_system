import sqlite3
from pathlib import Path
import hashlib
import secrets

STORAGE_DIR = Path(__file__).resolve().parents[1] / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = STORAGE_DIR / "auth.db"


def hash_password(password: str) -> str:
    """Hash password with salt"""
    salt = secrets.token_hex(32)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}${pwd_hash.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    try:
        salt, pwd_hash = hashed.split('$')
        new_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return new_hash.hex() == pwd_hash
    except:
        return False


def init_auth_db():
    """Initialize authentication database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hr_users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            department TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()


def create_hr_user(email: str, password: str, full_name: str, department: str = None):
    """Create a new HR user"""
    try:
        user_id = secrets.token_urlsafe(16)
        hashed_pwd = hash_password(password)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO hr_users (id, email, password, full_name, department)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, email, hashed_pwd, full_name, department))
        
        conn.commit()
        conn.close()
        
        return {
            'user_id': user_id,
            'email': email,
            'full_name': full_name,
            'department': department,
            'status': 'success'
        }
    except sqlite3.IntegrityError:
        raise ValueError(f"Email {email} already exists")
    except Exception as e:
        raise Exception(f"Error creating user: {str(e)}")


def authenticate_hr_user(email: str, password: str):
    """Authenticate HR user"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, email, password, full_name, department FROM hr_users WHERE email = ?
        ''', (email,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return None
        
        user_id, user_email, hashed_pwd, full_name, department = result
        
        if verify_password(password, hashed_pwd):
            return {
                'user_id': user_id,
                'email': user_email,
                'full_name': full_name,
                'department': department,
                'status': 'success'
            }
        else:
            return None
    except Exception as e:
        raise Exception(f"Error authenticating user: {str(e)}")


def get_hr_user(user_id: str):
    """Get HR user by ID"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, email, full_name, department FROM hr_users WHERE id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            user_id, email, full_name, department = result
            return {
                'user_id': user_id,
                'email': email,
                'full_name': full_name,
                'department': department
            }
        return None
    except Exception as e:
        raise Exception(f"Error getting user: {str(e)}")


def list_hr_users():
    """List all HR users"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, email, full_name, department FROM hr_users
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        users = []
        for user_id, email, full_name, department in results:
            users.append({
                'user_id': user_id,
                'email': email,
                'full_name': full_name,
                'department': department
            })
        
        return users
    except Exception as e:
        raise Exception(f"Error listing users: {str(e)}")
