import streamlit as st
import hashlib
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

class AuthManager:
    def __init__(self):
        self.users_file = Path("data/users.json")
        self.sessions_file = Path("data/sessions.json")
        self._ensure_data_dir()
        self._load_users()
        self._load_sessions()
    
    def _ensure_data_dir(self):
        """Ensure data directory exists"""
        Path("data").mkdir(exist_ok=True)
    
    def _load_users(self):
        """Load users from JSON file"""
        if self.users_file.exists():
            with open(self.users_file, 'r') as f:
                self.users = json.load(f)
        else:
            # Create default admin user
            self.users = {
                "admin": {
                    "username": "admin",
                    "password_hash": self._hash_password("Smita@280135"),
                    "role": "admin",
                    "name": "Administrator",
                    "email": "admin@trading.com",
                    "created_at": datetime.now().isoformat(),
                    "active": True
                }
            }
            self._save_users()
    
    def _load_sessions(self):
        """Load active sessions"""
        if self.sessions_file.exists():
            with open(self.sessions_file, 'r') as f:
                self.sessions = json.load(f)
        else:
            self.sessions = {}
    
    def _save_users(self):
        """Save users to JSON file"""
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=2)
    
    def _save_sessions(self):
        """Save sessions to JSON file"""
        with open(self.sessions_file, 'w') as f:
            json.dump(self.sessions, f, indent=2)
    
    def _hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions"""
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session_data in self.sessions.items():
            session_time = datetime.fromisoformat(session_data['created_at'])
            if current_time - session_time > timedelta(hours=24):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        if expired_sessions:
            self._save_sessions()
    
    def login(self, username, password):
        """Authenticate user login"""
        self._cleanup_expired_sessions()
        
        if username in self.users and self.users[username]['active']:
            if self.users[username]['password_hash'] == self._hash_password(password):
                # Create session
                session_id = self._generate_session_id()
                self.sessions[session_id] = {
                    'username': username,
                    'role': self.users[username]['role'],
                    'created_at': datetime.now().isoformat()
                }
                self._save_sessions()
                return session_id, self.users[username]['role']
        
        return None, None
    
    def _generate_session_id(self):
        """Generate unique session ID"""
        import secrets
        return secrets.token_urlsafe(32)
    
    def get_session_user(self, session_id):
        """Get user info from session"""
        if session_id in self.sessions:
            session_data = self.sessions[session_id]
            username = session_data['username']
            if username in self.users:
                return {
                    'username': username,
                    'role': session_data['role'],
                    'name': self.users[username]['name'],
                    'email': self.users[username]['email']
                }
        return None
    
    def logout(self, session_id):
        """Logout user by removing session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            self._save_sessions()
    
    def is_authenticated(self, session_id):
        """Check if session is valid"""
        return session_id in self.sessions
    
    def has_role(self, session_id, required_role):
        """Check if user has required role"""
        if session_id in self.sessions:
            user_role = self.sessions[session_id]['role']
            if required_role == 'admin':
                return user_role == 'admin'
            elif required_role == 'client':
                return user_role in ['admin', 'client']
        return False
    
    def create_client(self, username, password, name, email, starting_capital, investment_start_date=None):
        """Create new client account (admin only)"""
        if username not in self.users:
            if investment_start_date is None:
                investment_start_date = datetime.now().date()
            
            self.users[username] = {
                "username": username,
                "password_hash": self._hash_password(password),
                "role": "client",
                "name": name,
                "email": email,
                "starting_capital": starting_capital,
                "investment_start_date": investment_start_date.isoformat(),
                "created_at": datetime.now().isoformat(),
                "active": True
            }
            self._save_users()
            return True
        return False
    
    def update_user(self, username, **kwargs):
        """Update user information (admin only)"""
        if username in self.users:
            for key, value in kwargs.items():
                if key in ['name', 'email', 'active', 'starting_capital']:
                    self.users[username][key] = value
            self._save_users()
            return True
        return False
    
    def delete_user(self, username):
        """Delete user account (admin only)"""
        if username in self.users and username != 'admin':
            del self.users[username]
            self._save_users()
            return True
        return False
    
    def get_all_users(self):
        """Get all users (admin only)"""
        return self.users.copy()
    
    def change_password(self, username, new_password):
        """Change user password"""
        if username in self.users:
            self.users[username]['password_hash'] = self._hash_password(new_password)
            self._save_users()
            return True
        return False
    
    def load_users(self):
        """Load users data (public method)"""
        return self.users.copy()

def init_auth():
    """Initialize authentication in Streamlit session state"""
    if 'auth_manager' not in st.session_state:
        st.session_state.auth_manager = AuthManager()
    
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None
    
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None

def login_page():
    """Display login page"""
    st.title("🔐 Login - Trading Performance Dashboard")
    st.markdown("Please enter your credentials to access the dashboard.")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if username and password:
                session_id, role = st.session_state.auth_manager.login(username, password)
                if session_id:
                    st.session_state.session_id = session_id
                    st.session_state.user_info = st.session_state.auth_manager.get_session_user(session_id)
                    st.success(f"Welcome back, {st.session_state.user_info['name']}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.error("Please enter both username and password")
    
    # Admin credentials removed for security

def logout_button():
    """Display logout button in sidebar"""
    if st.session_state.session_id:
        if st.sidebar.button("🚪 Logout"):
            st.session_state.auth_manager.logout(st.session_state.session_id)
            st.session_state.session_id = None
            st.session_state.user_info = None
            st.success("Logged out successfully!")
            st.rerun()

def require_auth(required_role="client"):
    """Decorator to require authentication and role"""
    if not st.session_state.session_id:
        st.error("Please log in to access this page.")
        st.stop()
    
    # Handle both single role and list of roles
    if isinstance(required_role, list):
        # Check if user has any of the required roles
        has_permission = False
        for role in required_role:
            if st.session_state.auth_manager.has_role(st.session_state.session_id, role):
                has_permission = True
                break
        if not has_permission:
            st.error("You don't have permission to access this page.")
            st.stop()
    else:
        # Single role check
        if not st.session_state.auth_manager.has_role(st.session_state.session_id, required_role):
            st.error("You don't have permission to access this page.")
            st.stop()
    
    return st.session_state.user_info

