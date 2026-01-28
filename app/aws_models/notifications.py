"""SNS Notification helpers for FreshBakes."""

from app.aws_config import send_notification as _send_notification


def send_sns_notification(subject, message):
    """Send a notification via AWS SNS.
    
    Args:
        subject: Notification subject (max 100 chars)
        message: Notification message body
        
    Returns:
        bool: True if successful
    """
    return _send_notification(subject, message)


def notify_new_user_signup(email, name, role='customer'):
    """Send notification for new user signup.
    
    Args:
        email: User's email
        name: User's name
        role: User role
        
    Returns:
        bool: True if successful
    """
    subject = f"New {role.title()} Signup - FreshBakes"
    message = f"""
New user registered on FreshBakes!

Name: {name}
Email: {email}
Role: {role}

Login to admin dashboard to manage users.
"""
    return _send_notification(subject, message)


def notify_new_order(order_number, customer_email, bakery_name, total_amount, items_count):
    """Send notification for new order.
    
    Args:
        order_number: Order number
        customer_email: Customer's email
        bakery_name: Bakery name
        total_amount: Order total
        items_count: Number of items
        
    Returns:
        bool: True if successful
    """
    subject = f"New Order {order_number} - FreshBakes"
    message = f"""
New order received!

Order Number: {order_number}
Customer: {customer_email}
Bakery: {bakery_name}
Items: {items_count}
Total Amount: ${total_amount:.2f}

Please process this order promptly.
"""
    return _send_notification(subject, message)


def notify_order_status_change(order_number, customer_email, old_status, new_status):
    """Send notification for order status change.
    
    Args:
        order_number: Order number
        customer_email: Customer's email
        old_status: Previous status
        new_status: New status
        
    Returns:
        bool: True if successful
    """
    status_messages = {
        'confirmed': 'Your order has been confirmed by the bakery!',
        'preparing': 'The bakery is now preparing your delicious treats!',
        'ready': 'Your order is ready for pickup/delivery!',
        'out_for_delivery': 'Your order is on its way!',
        'delivered': 'Your order has been delivered. Enjoy your treats!',
        'cancelled': 'Your order has been cancelled.'
    }
    
    status_description = status_messages.get(
        new_status, 
        f'Your order status has been updated to: {new_status}'
    )
    
    subject = f"Order {order_number} - {new_status.replace('_', ' ').title()}"
    message = f"""
Order Status Update

Order Number: {order_number}
Customer: {customer_email}

{status_description}

Previous Status: {old_status}
New Status: {new_status}

Thank you for choosing FreshBakes!
"""
    return _send_notification(subject, message)


def notify_bakery_approved(bakery_name, owner_email):
    """Send notification when bakery is approved.
    
    Args:
        bakery_name: Bakery name
        owner_email: Owner's email
        
    Returns:
        bool: True if successful
    """
    subject = f"Bakery Approved - {bakery_name}"
    message = f"""
Congratulations!

Your bakery "{bakery_name}" has been approved on FreshBakes!

Owner: {owner_email}

You can now:
- Add products to your menu
- Start receiving orders
- Manage your bakery profile

Login to your baker dashboard to get started!
"""
    return _send_notification(subject, message)


def notify_new_review(bakery_name, order_number, rating, comment=None):
    """Send notification for new review.
    
    Args:
        bakery_name: Bakery name
        order_number: Associated order number
        rating: Star rating (1-5)
        comment: Review comment
        
    Returns:
        bool: True if successful
    """
    stars = '⭐' * rating
    subject = f"New Review for {bakery_name}"
    message = f"""
New review received!

Bakery: {bakery_name}
Order: {order_number}
Rating: {stars} ({rating}/5)

Comment: {comment or 'No comment provided'}

Reply to this review from your baker dashboard.
"""
    return _send_notification(subject, message)


def notify_low_stock(product_name, bakery_name, current_stock, threshold=5):
    """Send notification for low stock alert.
    
    Args:
        product_name: Product name
        bakery_name: Bakery name
        current_stock: Current stock quantity
        threshold: Low stock threshold
        
    Returns:
        bool: True if successful
    """
    subject = f"Low Stock Alert - {product_name}"
    message = f"""
Low Stock Warning!

Product: {product_name}
Bakery: {bakery_name}
Current Stock: {current_stock}
Threshold: {threshold}

Please restock this item soon to avoid running out.
"""
    return _send_notification(subject, message)
