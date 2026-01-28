"""DynamoDB operations for Reviews table."""

import uuid
from datetime import datetime
from botocore.exceptions import ClientError
from app.aws_config import reviews_table


def create_review(user_email, bakery_id, order_number, rating, 
                  comment=None, product_id=None):
    """Create a new review.
    
    Args:
        user_email: Reviewer's email
        bakery_id: Bakery UUID
        order_number: Associated order number
        rating: Rating (1-5)
        comment: Review comment
        product_id: Optional product UUID for product-specific review
        
    Returns:
        dict: Created review data or None on error
    """
    try:
        review_id = str(uuid.uuid4())
        
        review_data = {
            'id': review_id,
            'user_email': user_email.lower(),
            'bakery_id': bakery_id,
            'order_number': order_number,
            'product_id': product_id or '',
            'rating': int(rating),
            'comment': comment or '',
            'reply': '',
            'reply_at': '',
            'is_visible': True,
            'created_at': datetime.utcnow().isoformat()
        }
        
        reviews_table.put_item(Item=review_data)
        return review_data
    except ClientError as e:
        print(f"Error creating review: {e}")
        return None


def get_review_by_id(review_id):
    """Get a review by ID.
    
    Args:
        review_id: Review UUID
        
    Returns:
        dict: Review data or None
    """
    try:
        response = reviews_table.get_item(Key={'id': review_id})
        return response.get('Item')
    except ClientError as e:
        print(f"Error getting review: {e}")
        return None


def get_reviews_by_bakery(bakery_id, visible_only=True):
    """Get all reviews for a bakery.
    
    Args:
        bakery_id: Bakery UUID
        visible_only: Only return visible reviews
        
    Returns:
        list: List of reviews
    """
    try:
        filter_expr = 'bakery_id = :bid'
        expr_values = {':bid': bakery_id}
        
        if visible_only:
            filter_expr += ' AND is_visible = :visible'
            expr_values[':visible'] = True
        
        response = reviews_table.scan(
            FilterExpression=filter_expr,
            ExpressionAttributeValues=expr_values
        )
        
        items = response.get('Items', [])
        return sorted(items, key=lambda x: x.get('created_at', ''), reverse=True)
    except ClientError as e:
        print(f"Error getting reviews by bakery: {e}")
        return []


def get_reviews_by_product(product_id, visible_only=True):
    """Get all reviews for a product.
    
    Args:
        product_id: Product UUID
        visible_only: Only return visible reviews
        
    Returns:
        list: List of reviews
    """
    try:
        filter_expr = 'product_id = :pid'
        expr_values = {':pid': product_id}
        
        if visible_only:
            filter_expr += ' AND is_visible = :visible'
            expr_values[':visible'] = True
        
        response = reviews_table.scan(
            FilterExpression=filter_expr,
            ExpressionAttributeValues=expr_values
        )
        
        items = response.get('Items', [])
        return sorted(items, key=lambda x: x.get('created_at', ''), reverse=True)
    except ClientError as e:
        print(f"Error getting reviews by product: {e}")
        return []


def get_reviews_by_user(user_email):
    """Get all reviews by a user.
    
    Args:
        user_email: User's email
        
    Returns:
        list: List of reviews
    """
    try:
        response = reviews_table.scan(
            FilterExpression='user_email = :email',
            ExpressionAttributeValues={':email': user_email.lower()}
        )
        
        items = response.get('Items', [])
        return sorted(items, key=lambda x: x.get('created_at', ''), reverse=True)
    except ClientError as e:
        print(f"Error getting reviews by user: {e}")
        return []


def add_reply(review_id, reply_text):
    """Add a baker's reply to a review.
    
    Args:
        review_id: Review UUID
        reply_text: Reply message
        
    Returns:
        bool: True if successful
    """
    try:
        reviews_table.update_item(
            Key={'id': review_id},
            UpdateExpression="SET reply = :reply, reply_at = :reply_at",
            ExpressionAttributeValues={
                ':reply': reply_text,
                ':reply_at': datetime.utcnow().isoformat()
            }
        )
        return True
    except ClientError as e:
        print(f"Error adding reply: {e}")
        return False


def hide_review(review_id):
    """Hide a review (admin/moderation).
    
    Args:
        review_id: Review UUID
        
    Returns:
        bool: True if successful
    """
    try:
        reviews_table.update_item(
            Key={'id': review_id},
            UpdateExpression="SET is_visible = :visible",
            ExpressionAttributeValues={':visible': False}
        )
        return True
    except ClientError as e:
        print(f"Error hiding review: {e}")
        return False


def calculate_bakery_rating(bakery_id):
    """Calculate average rating for a bakery.
    
    Args:
        bakery_id: Bakery UUID
        
    Returns:
        tuple: (average_rating, total_reviews)
    """
    reviews = get_reviews_by_bakery(bakery_id, visible_only=True)
    
    if not reviews:
        return (0.0, 0)
    
    total_rating = sum(r.get('rating', 0) for r in reviews)
    avg_rating = total_rating / len(reviews)
    
    return (round(avg_rating, 1), len(reviews))
