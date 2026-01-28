"""DynamoDB operations for Users table."""

import uuid
from datetime import datetime
from flask_bcrypt import Bcrypt
from botocore.exceptions import ClientError
from app.aws_config import users_table, send_notification

# Initialize bcrypt for password hashing
bcrypt = Bcrypt()


def get_user_by_email(email):
    """Get a user by email (primary key).
    
    Args:
        email: User's email address
        
    Returns:
        dict: User data or None if not found
    """
    try:
        response = users_table.get_item(Key={'email': email.lower()})
        return response.get('Item')
    except ClientError as e:
        print(f"Error getting user: {e}")
        return None


def create_user(email, password, name, phone=None, role='customer', profile_image='default-avatar.png'):
    """Create a new user with bcrypt password hashing.
    
    Args:
        email: User's email
        password: Plain text password (will be hashed)
        name: User's full name
        phone: Optional phone number
        role: User role (customer, baker, admin)
        profile_image: Profile image filename
        
    Returns:
        dict: Created user data or None on error
    """
    try:
        # Check if user already exists
        existing = get_user_by_email(email)
        if existing:
            return None
        
        # Hash password using bcrypt
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        
        user_data = {
            'email': email.lower(),
            'password_hash': password_hash,
            'name': name,
            'phone': phone or '',
            'profile_image': profile_image,
            'role': role,
            'is_active': True,
            'email_verified': False,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        users_table.put_item(Item=user_data)
        
        # Send notification for new signup
        send_notification(
            "New User Signup",
            f"New {role} registered: {name} ({email})"
        )
        
        return user_data
    except ClientError as e:
        print(f"Error creating user: {e}")
        return None


def verify_password(email, password):
    """Verify user credentials.
    
    Args:
        email: User's email
        password: Plain text password to verify
        
    Returns:
        dict: User data if valid, None if invalid
    """
    user = get_user_by_email(email)
    if user and bcrypt.check_password_hash(user.get('password_hash', ''), password):
        if user.get('is_active', True):
            return user
    return None


def update_user(email, updates):
    """Update user attributes.
    
    Args:
        email: User's email (primary key)
        updates: Dictionary of attributes to update
        
    Returns:
        bool: True if successful
    """
    try:
        # Build update expression
        update_expr = "SET updated_at = :updated_at"
        expr_values = {':updated_at': datetime.utcnow().isoformat()}
        
        for key, value in updates.items():
            if key not in ['email', 'password_hash']:  # Don't allow changing PK or direct password update
                update_expr += f", {key} = :{key}"
                expr_values[f':{key}'] = value
        
        users_table.update_item(
            Key={'email': email.lower()},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values
        )
        return True
    except ClientError as e:
        print(f"Error updating user: {e}")
        return False


def update_password(email, new_password):
    """Update user's password with bcrypt hashing.
    
    Args:
        email: User's email
        new_password: New plain text password
        
    Returns:
        bool: True if successful
    """
    try:
        password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
        users_table.update_item(
            Key={'email': email.lower()},
            UpdateExpression="SET password_hash = :ph, updated_at = :ua",
            ExpressionAttributeValues={
                ':ph': password_hash,
                ':ua': datetime.utcnow().isoformat()
            }
        )
        return True
    except ClientError as e:
        print(f"Error updating password: {e}")
        return False


def get_all_users():
    """Get all users (admin function).
    
    Returns:
        list: List of all user records
    """
    try:
        response = users_table.scan()
        return response.get('Items', [])
    except ClientError as e:
        print(f"Error scanning users: {e}")
        return []


def get_users_by_role(role):
    """Get users by role using GSI.
    
    Args:
        role: User role to filter by
        
    Returns:
        list: List of users with specified role
    """
    try:
        response = users_table.query(
            IndexName='role-index',
            KeyConditionExpression='#r = :role',
            ExpressionAttributeNames={'#r': 'role'},
            ExpressionAttributeValues={':role': role}
        )
        return response.get('Items', [])
    except ClientError as e:
        print(f"Error querying users by role: {e}")
        # Fallback to scan with filter
        try:
            response = users_table.scan(
                FilterExpression='#r = :role',
                ExpressionAttributeNames={'#r': 'role'},
                ExpressionAttributeValues={':role': role}
            )
            return response.get('Items', [])
        except:
            return []


def deactivate_user(email):
    """Deactivate a user account.
    
    Args:
        email: User's email
        
    Returns:
        bool: True if successful
    """
    return update_user(email, {'is_active': False})


def activate_user(email):
    """Activate a user account.
    
    Args:
        email: User's email
        
    Returns:
        bool: True if successful
    """
    return update_user(email, {'is_active': True})
