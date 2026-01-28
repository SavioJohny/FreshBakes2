"""DynamoDB operations for Cart table."""

from datetime import datetime
from botocore.exceptions import ClientError
from app.aws_config import cart_table


def get_cart_items(user_email):
    """Get all cart items for a user.
    
    Args:
        user_email: User's email
        
    Returns:
        list: List of cart items
    """
    try:
        response = cart_table.query(
            KeyConditionExpression='user_email = :email',
            ExpressionAttributeValues={':email': user_email.lower()}
        )
        return response.get('Items', [])
    except ClientError as e:
        print(f"Error getting cart items: {e}")
        return []


def get_cart_item(user_email, product_id):
    """Get a specific cart item.
    
    Args:
        user_email: User's email
        product_id: Product UUID
        
    Returns:
        dict: Cart item or None
    """
    try:
        response = cart_table.get_item(
            Key={
                'user_email': user_email.lower(),
                'product_id': product_id
            }
        )
        return response.get('Item')
    except ClientError as e:
        print(f"Error getting cart item: {e}")
        return None


def add_to_cart(user_email, product_id, product_name, quantity=1, 
                unit_price=0.0, special_instructions=None):
    """Add an item to cart or update quantity if exists.
    
    Args:
        user_email: User's email
        product_id: Product UUID
        product_name: Product name (for display)
        quantity: Quantity to add
        unit_price: Price per unit
        special_instructions: Special instructions
        
    Returns:
        dict: Cart item data or None on error
    """
    try:
        existing = get_cart_item(user_email, product_id)
        
        if existing:
            # Update quantity
            new_quantity = existing.get('quantity', 0) + quantity
            return update_cart_item(user_email, product_id, new_quantity)
        
        # Create new cart item
        cart_item = {
            'user_email': user_email.lower(),
            'product_id': product_id,
            'product_name': product_name,
            'quantity': int(quantity),
            'unit_price': float(unit_price),
            'special_instructions': special_instructions or '',
            'created_at': datetime.utcnow().isoformat()
        }
        
        cart_table.put_item(Item=cart_item)
        return cart_item
    except ClientError as e:
        print(f"Error adding to cart: {e}")
        return None


def update_cart_item(user_email, product_id, quantity, special_instructions=None):
    """Update cart item quantity.
    
    Args:
        user_email: User's email
        product_id: Product UUID
        quantity: New quantity
        special_instructions: Optional new instructions
        
    Returns:
        dict: Updated cart item or None
    """
    try:
        if quantity <= 0:
            return remove_from_cart(user_email, product_id)
        
        update_expr = "SET quantity = :qty"
        expr_values = {':qty': int(quantity)}
        
        if special_instructions is not None:
            update_expr += ", special_instructions = :inst"
            expr_values[':inst'] = special_instructions
        
        cart_table.update_item(
            Key={
                'user_email': user_email.lower(),
                'product_id': product_id
            },
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values
        )
        
        return get_cart_item(user_email, product_id)
    except ClientError as e:
        print(f"Error updating cart item: {e}")
        return None


def remove_from_cart(user_email, product_id):
    """Remove an item from cart.
    
    Args:
        user_email: User's email
        product_id: Product UUID
        
    Returns:
        bool: True if successful
    """
    try:
        cart_table.delete_item(
            Key={
                'user_email': user_email.lower(),
                'product_id': product_id
            }
        )
        return True
    except ClientError as e:
        print(f"Error removing from cart: {e}")
        return False


def clear_cart(user_email):
    """Remove all items from user's cart.
    
    Args:
        user_email: User's email
        
    Returns:
        bool: True if successful
    """
    try:
        items = get_cart_items(user_email)
        
        for item in items:
            cart_table.delete_item(
                Key={
                    'user_email': user_email.lower(),
                    'product_id': item['product_id']
                }
            )
        
        return True
    except ClientError as e:
        print(f"Error clearing cart: {e}")
        return False


def get_cart_total(user_email):
    """Calculate cart total for a user.
    
    Args:
        user_email: User's email
        
    Returns:
        dict: Cart summary with item_count and total
    """
    items = get_cart_items(user_email)
    
    total = 0.0
    item_count = 0
    
    for item in items:
        quantity = item.get('quantity', 0)
        unit_price = item.get('unit_price', 0)
        total += quantity * unit_price
        item_count += quantity
    
    return {
        'item_count': item_count,
        'total': round(total, 2),
        'items': items
    }
