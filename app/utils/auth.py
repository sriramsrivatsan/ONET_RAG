"""
Authentication module for password protection
Uses environment variable M_PASSWORD for access control
"""
import os
import streamlit as st
from typing import Optional


def get_required_password() -> Optional[str]:
    """
    Get the required password from environment variable
    
    Returns:
        Password string if set, None if not configured
    """
    return os.environ.get('M_PASSWORD')


def is_authentication_required() -> bool:
    """
    Check if authentication is required (M_PASSWORD is set)
    
    Returns:
        True if password is required, False otherwise
    """
    return get_required_password() is not None


def is_authenticated() -> bool:
    """
    Check if user is authenticated in current session
    
    Returns:
        True if authenticated, False otherwise
    """
    return st.session_state.get('authenticated', False)


def authenticate(password: str) -> bool:
    """
    Authenticate user with provided password
    
    Args:
        password: Password to check
        
    Returns:
        True if password is correct, False otherwise
    """
    required_password = get_required_password()
    
    # If no password is set, allow access
    if required_password is None:
        return True
    
    # Check if password matches
    if password == required_password:
        st.session_state.authenticated = True
        return True
    
    return False


def logout():
    """Logout user by clearing authentication state"""
    if 'authenticated' in st.session_state:
        del st.session_state.authenticated


def render_login_dialog():
    """
    Render login dialog for password entry
    This should be called before any protected content
    """
    
    # Check if authentication is required
    if not is_authentication_required():
        # No password set, grant access
        st.session_state.authenticated = True
        return
    
    # Check if already authenticated
    if is_authenticated():
        return
    
    # Show login dialog
    st.markdown("""
    <style>
    .login-container {
        max-width: 400px;
        margin: 100px auto;
        padding: 40px;
        border-radius: 10px;
        background: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔒 Authentication Required")
        st.markdown("Please enter the password to access the system.")
        
        with st.form("login_form", clear_on_submit=True):
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter password",
                key="password_input"
            )
            
            submit = st.form_submit_button("🔓 Login", use_container_width=True)
            
            if submit:
                if authenticate(password):
                    st.success("✅ Authentication successful!")
                    st.rerun()
                else:
                    st.error("❌ Incorrect password. Please try again.")


def require_authentication(func):
    """
    Decorator to require authentication for a function
    
    Usage:
        @require_authentication
        def protected_function():
            # This will only run if authenticated
            pass
    """
    def wrapper(*args, **kwargs):
        if not is_authentication_required():
            # No password required
            return func(*args, **kwargs)
        
        if not is_authenticated():
            # Not authenticated, show login
            render_login_dialog()
            st.stop()
        
        # Authenticated, run function
        return func(*args, **kwargs)
    
    return wrapper
