"""DynamoDB operations for Bakeries table."""

import uuid
from datetime import datetime
from slugify import slugify
from botocore.exceptions import ClientError
from app.aws_config import bakeries_table, send_notification


def get_bakery_by_id(bakery_id):
    """Get a bakery by ID (primary key).
    
    Args:
        bakery_id: Bakery UUID
        
    Returns:
        dict: Bakery data or None if not found
    """
    try:
        response = bakeries_table.get_item(Key={'id': bakery_id})
        return response.get('Item')
    except ClientError as e:
        print(f"Error getting bakery: {e}")
        return None


def get_bakery_by_owner(owner_email):
    """Get bakery by owner email using GSI.
    
    Args:
        owner_email: Owner's email address
        
    Returns:
        dict: Bakery data or None
    """
    try:
        response = bakeries_table.query(
            IndexName='owner_email-index',
            KeyConditionExpression='owner_email = :email',
            ExpressionAttributeValues={':email': owner_email.lower()}
        )
        items = response.get('Items', [])
        return items[0] if items else None
    except ClientError as e:
        print(f"Error querying bakery by owner: {e}")
        return None


def get_bakery_by_slug(slug):
    """Get bakery by slug.
    
    Args:
        slug: Bakery URL slug
        
    Returns:
        dict: Bakery data or None
    """
    try:
        response = bakeries_table.scan(
            FilterExpression='slug = :slug',
            ExpressionAttributeValues={':slug': slug}
        )
        items = response.get('Items', [])
        return items[0] if items else None
    except ClientError as e:
        print(f"Error finding bakery by slug: {e}")
        return None


def generate_unique_slug(name):
    """Generate a unique slug for a bakery.
    
    Args:
        name: Bakery name
        
    Returns:
        str: Unique slug
    """
    base_slug = slugify(name) if name else 'bakery'
    slug = base_slug
    counter = 1
    
    while get_bakery_by_slug(slug) is not None:
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    return slug


def create_bakery(owner_email, name, description, address, city, pincode,
                  phone=None, email=None, min_order_amount=0.0, 
                  delivery_fee=0.0, delivery_time_mins=30):
    """Create a new bakery.
    
    Args:
        owner_email: Owner's email
        name: Bakery name
        description: Bakery description
        address: Street address
        city: City name
        pincode: Postal code
        phone: Optional phone number
        email: Optional bakery email
        min_order_amount: Minimum order value
        delivery_fee: Delivery charge
        delivery_time_mins: Estimated delivery time
        
    Returns:
        dict: Created bakery data or None on error
    """
    try:
        bakery_id = str(uuid.uuid4())
        slug = generate_unique_slug(name)
        
        default_hours = {
            'monday': {'open': '09:00', 'close': '21:00', 'is_open': True},
            'tuesday': {'open': '09:00', 'close': '21:00', 'is_open': True},
            'wednesday': {'open': '09:00', 'close': '21:00', 'is_open': True},
            'thursday': {'open': '09:00', 'close': '21:00', 'is_open': True},
            'friday': {'open': '09:00', 'close': '21:00', 'is_open': True},
            'saturday': {'open': '09:00', 'close': '22:00', 'is_open': True},
            'sunday': {'open': '10:00', 'close': '20:00', 'is_open': True},
        }
        
        bakery_data = {
            'id': bakery_id,
            'owner_email': owner_email.lower(),
            'name': name,
            'slug': slug,
            'description': description or '',
            'address': address,
            'city': city,
            'pincode': pincode,
            'phone': phone or '',
            'email': email or owner_email.lower(),
            'logo_url': 'default-bakery.png',
            'banner_url': '',
            'rating': 0.0,
            'total_reviews': 0,
            'min_order_amount': float(min_order_amount),
            'delivery_fee': float(delivery_fee),
            'delivery_time_mins': int(delivery_time_mins),
            'is_approved': False,
            'is_open': True,
            'is_featured': False,
            'operating_hours': default_hours,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        bakeries_table.put_item(Item=bakery_data)
        
        send_notification(
            "New Bakery Registration",
            f"New bakery '{name}' registered by {owner_email}. Pending approval."
        )
        
        return bakery_data
    except ClientError as e:
        print(f"Error creating bakery: {e}")
        return None


def update_bakery(bakery_id, updates):
    """Update bakery attributes.
    
    Args:
        bakery_id: Bakery UUID
        updates: Dictionary of attributes to update
        
    Returns:
        bool: True if successful
    """
    try:
        update_expr = "SET updated_at = :updated_at"
        expr_values = {':updated_at': datetime.utcnow().isoformat()}
        
        for key, value in updates.items():
            if key not in ['id', 'owner_email']:  # Don't allow changing PK or owner
                update_expr += f", {key} = :{key}"
                expr_values[f':{key}'] = value
        
        bakeries_table.update_item(
            Key={'id': bakery_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values
        )
        return True
    except ClientError as e:
        print(f"Error updating bakery: {e}")
        return False


def approve_bakery(bakery_id):
    """Approve a bakery for operation.
    
    Args:
        bakery_id: Bakery UUID
        
    Returns:
        bool: True if successful
    """
    bakery = get_bakery_by_id(bakery_id)
    if bakery:
        result = update_bakery(bakery_id, {'is_approved': True})
        if result:
            send_notification(
                "Bakery Approved",
                f"Bakery '{bakery.get('name')}' has been approved!"
            )
        return result
    return False


def get_all_bakeries():
    """Get all bakeries.
    
    Returns:
        list: List of all bakery records
    """
    try:
        response = bakeries_table.scan()
        return response.get('Items', [])
    except ClientError as e:
        print(f"Error scanning bakeries: {e}")
        return []


def get_approved_bakeries():
    """Get all approved bakeries.
    
    Returns:
        list: List of approved bakeries
    """
    try:
        response = bakeries_table.scan(
            FilterExpression='is_approved = :approved',
            ExpressionAttributeValues={':approved': True}
        )
        return response.get('Items', [])
    except ClientError as e:
        print(f"Error getting approved bakeries: {e}")
        return []


def get_featured_bakeries():
    """Get featured bakeries.
    
    Returns:
        list: List of featured bakeries
    """
    try:
        response = bakeries_table.scan(
            FilterExpression='is_featured = :featured AND is_approved = :approved',
            ExpressionAttributeValues={
                ':featured': True,
                ':approved': True
            }
        )
        return response.get('Items', [])
    except ClientError as e:
        print(f"Error getting featured bakeries: {e}")
        return []


def update_bakery_rating(bakery_id, new_rating, total_reviews):
    """Update bakery rating statistics.
    
    Args:
        bakery_id: Bakery UUID
        new_rating: Calculated average rating
        total_reviews: Total number of reviews
        
    Returns:
        bool: True if successful
    """
    return update_bakery(bakery_id, {
        'rating': float(new_rating),
        'total_reviews': int(total_reviews)
    })
