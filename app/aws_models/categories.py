"""DynamoDB operations for Categories table."""

import uuid
from datetime import datetime
from botocore.exceptions import ClientError
from app.aws_config import categories_table


def get_category_by_id(category_id):
    """Get a category by ID.
    
    Args:
        category_id: Category UUID
        
    Returns:
        dict: Category data or None
    """
    try:
        response = categories_table.get_item(Key={'id': category_id})
        return response.get('Item')
    except ClientError as e:
        print(f"Error getting category: {e}")
        return None


def get_categories_by_bakery(bakery_id, active_only=True):
    """Get all categories for a bakery.
    
    Args:
        bakery_id: Bakery UUID
        active_only: Only return active categories
        
    Returns:
        list: List of categories sorted by display_order
    """
    try:
        filter_expr = 'bakery_id = :bid'
        expr_values = {':bid': bakery_id}
        
        if active_only:
            filter_expr += ' AND is_active = :active'
            expr_values[':active'] = True
        
        response = categories_table.scan(
            FilterExpression=filter_expr,
            ExpressionAttributeValues=expr_values
        )
        
        items = response.get('Items', [])
        return sorted(items, key=lambda x: x.get('display_order', 0))
    except ClientError as e:
        print(f"Error getting categories by bakery: {e}")
        return []


def create_category(bakery_id, name, description=None, display_order=0):
    """Create a new category.
    
    Args:
        bakery_id: Bakery UUID
        name: Category name
        description: Category description
        display_order: Display order for sorting
        
    Returns:
        dict: Created category data or None on error
    """
    try:
        category_id = str(uuid.uuid4())
        
        category_data = {
            'id': category_id,
            'bakery_id': bakery_id,
            'name': name,
            'description': description or '',
            'display_order': int(display_order),
            'is_active': True,
            'created_at': datetime.utcnow().isoformat()
        }
        
        categories_table.put_item(Item=category_data)
        return category_data
    except ClientError as e:
        print(f"Error creating category: {e}")
        return None


def update_category(category_id, updates):
    """Update category attributes.
    
    Args:
        category_id: Category UUID
        updates: Dictionary of attributes to update
        
    Returns:
        bool: True if successful
    """
    try:
        update_expr_parts = []
        expr_values = {}
        
        for key, value in updates.items():
            if key not in ['id', 'bakery_id']:  # Don't allow changing PK or bakery
                update_expr_parts.append(f"{key} = :{key}")
                expr_values[f':{key}'] = value
        
        if not update_expr_parts:
            return True
        
        update_expr = "SET " + ", ".join(update_expr_parts)
        
        categories_table.update_item(
            Key={'id': category_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values
        )
        return True
    except ClientError as e:
        print(f"Error updating category: {e}")
        return False


def delete_category(category_id):
    """Delete a category.
    
    Args:
        category_id: Category UUID
        
    Returns:
        bool: True if successful
    """
    try:
        categories_table.delete_item(Key={'id': category_id})
        return True
    except ClientError as e:
        print(f"Error deleting category: {e}")
        return False


def deactivate_category(category_id):
    """Deactivate a category (soft delete).
    
    Args:
        category_id: Category UUID
        
    Returns:
        bool: True if successful
    """
    return update_category(category_id, {'is_active': False})
