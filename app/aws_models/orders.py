"""DynamoDB operations for Orders table."""

import uuid
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
from app.aws_config import orders_table, send_notification


def generate_order_number():
    """Generate a unique order number.
    
    Returns:
        str: Unique order number (e.g., FB202601281234ABCDEF)
    """
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M')
    unique_id = str(uuid.uuid4().hex)[:6].upper()
    return f'FB{timestamp}{unique_id}'


def create_order(customer_email, bakery_id, items, delivery_address,
                 subtotal, delivery_fee=0.0, discount=0.0,
                 payment_method='cod', special_instructions=None):
    """Create a new order.
    
    Args:
        customer_email: Customer's email
        bakery_id: Bakery UUID
        items: List of order items (each with product_id, product_name, quantity, unit_price, subtotal)
        delivery_address: Delivery address dict
        subtotal: Order subtotal
        delivery_fee: Delivery fee
        discount: Discount amount
        payment_method: Payment method (cod, online)
        special_instructions: Special delivery instructions
        
    Returns:
        dict: Created order data or None on error
    """
    try:
        order_number = generate_order_number()
        total_amount = float(subtotal) + float(delivery_fee) - float(discount)
        
        # Estimate delivery time (bakery delivery_time + 15 mins buffer)
        estimated_delivery = (datetime.utcnow() + timedelta(minutes=45)).isoformat()
        
        order_data = {
            'order_number': order_number,
            'customer_email': customer_email.lower(),
            'bakery_id': bakery_id,
            'items': items,  # Store as nested list in DynamoDB
            'delivery_address': delivery_address,
            'subtotal': float(subtotal),
            'delivery_fee': float(delivery_fee),
            'discount': float(discount),
            'total_amount': total_amount,
            'status': 'pending',
            'payment_method': payment_method,
            'payment_status': 'pending',
            'special_instructions': special_instructions or '',
            'cancellation_reason': '',
            'estimated_delivery': estimated_delivery,
            'delivered_at': '',
            'status_history': [
                {
                    'status': 'pending',
                    'timestamp': datetime.utcnow().isoformat(),
                    'notes': 'Order placed'
                }
            ],
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        orders_table.put_item(Item=order_data)
        
        # Send notification
        send_notification(
            "New Order Placed",
            f"Order {order_number} placed by {customer_email}. Total: ${total_amount:.2f}"
        )
        
        return order_data
    except ClientError as e:
        print(f"Error creating order: {e}")
        return None


def get_order_by_number(order_number):
    """Get an order by order number (primary key).
    
    Args:
        order_number: Order number
        
    Returns:
        dict: Order data or None
    """
    try:
        response = orders_table.get_item(Key={'order_number': order_number})
        return response.get('Item')
    except ClientError as e:
        print(f"Error getting order: {e}")
        return None


def get_orders_by_customer(customer_email):
    """Get all orders for a customer using GSI.
    
    Args:
        customer_email: Customer's email
        
    Returns:
        list: List of orders
    """
    try:
        response = orders_table.query(
            IndexName='customer_email-index',
            KeyConditionExpression='customer_email = :email',
            ExpressionAttributeValues={':email': customer_email.lower()},
            ScanIndexForward=False  # Sort descending (newest first)
        )
        return response.get('Items', [])
    except ClientError as e:
        print(f"Error querying orders by customer: {e}")
        # Fallback to scan
        try:
            response = orders_table.scan(
                FilterExpression='customer_email = :email',
                ExpressionAttributeValues={':email': customer_email.lower()}
            )
            items = response.get('Items', [])
            return sorted(items, key=lambda x: x.get('created_at', ''), reverse=True)
        except:
            return []


def get_orders_by_bakery(bakery_id, status=None):
    """Get all orders for a bakery using GSI.
    
    Args:
        bakery_id: Bakery UUID
        status: Optional status filter
        
    Returns:
        list: List of orders
    """
    try:
        filter_expr = 'bakery_id = :bid'
        expr_values = {':bid': bakery_id}
        
        if status:
            filter_expr += ' AND #status = :status'
            response = orders_table.scan(
                FilterExpression=filter_expr,
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={**expr_values, ':status': status}
            )
        else:
            response = orders_table.scan(
                FilterExpression=filter_expr,
                ExpressionAttributeValues=expr_values
            )
        
        items = response.get('Items', [])
        return sorted(items, key=lambda x: x.get('created_at', ''), reverse=True)
    except ClientError as e:
        print(f"Error querying orders by bakery: {e}")
        return []


def update_order_status(order_number, new_status, notes=None):
    """Update order status and add to history.
    
    Args:
        order_number: Order number
        new_status: New status value
        notes: Optional status change notes
        
    Returns:
        bool: True if successful
    """
    try:
        order = get_order_by_number(order_number)
        if not order:
            return False
        
        # Add to status history
        status_history = order.get('status_history', [])
        status_history.append({
            'status': new_status,
            'timestamp': datetime.utcnow().isoformat(),
            'notes': notes or f'Status changed to {new_status}'
        })
        
        update_data = {
            'status': new_status,
            'status_history': status_history,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Set delivered_at if delivered
        if new_status == 'delivered':
            update_data['delivered_at'] = datetime.utcnow().isoformat()
        
        # Build update expression
        update_expr = "SET #status = :status, status_history = :history, updated_at = :updated"
        expr_values = {
            ':status': new_status,
            ':history': status_history,
            ':updated': update_data['updated_at']
        }
        expr_names = {'#status': 'status'}
        
        if new_status == 'delivered':
            update_expr += ", delivered_at = :delivered"
            expr_values[':delivered'] = update_data['delivered_at']
        
        orders_table.update_item(
            Key={'order_number': order_number},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values
        )
        
        # Send notification
        send_notification(
            f"Order {new_status.replace('_', ' ').title()}",
            f"Order {order_number} status updated to: {new_status}"
        )
        
        return True
    except ClientError as e:
        print(f"Error updating order status: {e}")
        return False


def cancel_order(order_number, reason=None):
    """Cancel an order.
    
    Args:
        order_number: Order number
        reason: Cancellation reason
        
    Returns:
        bool: True if successful
    """
    try:
        order = get_order_by_number(order_number)
        if not order:
            return False
        
        # Can only cancel pending or confirmed orders
        if order.get('status') not in ['pending', 'confirmed']:
            return False
        
        orders_table.update_item(
            Key={'order_number': order_number},
            UpdateExpression="SET #status = :status, cancellation_reason = :reason, updated_at = :updated",
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'cancelled',
                ':reason': reason or 'Order cancelled',
                ':updated': datetime.utcnow().isoformat()
            }
        )
        
        send_notification(
            "Order Cancelled",
            f"Order {order_number} has been cancelled. Reason: {reason or 'Not specified'}"
        )
        
        return True
    except ClientError as e:
        print(f"Error cancelling order: {e}")
        return False


def update_payment_status(order_number, payment_status):
    """Update order payment status.
    
    Args:
        order_number: Order number
        payment_status: New payment status (pending, paid, failed, refunded)
        
    Returns:
        bool: True if successful
    """
    try:
        orders_table.update_item(
            Key={'order_number': order_number},
            UpdateExpression="SET payment_status = :ps, updated_at = :updated",
            ExpressionAttributeValues={
                ':ps': payment_status,
                ':updated': datetime.utcnow().isoformat()
            }
        )
        return True
    except ClientError as e:
        print(f"Error updating payment status: {e}")
        return False


def get_all_orders():
    """Get all orders (admin function).
    
    Returns:
        list: List of all orders
    """
    try:
        response = orders_table.scan()
        items = response.get('Items', [])
        return sorted(items, key=lambda x: x.get('created_at', ''), reverse=True)
    except ClientError as e:
        print(f"Error scanning orders: {e}")
        return []
