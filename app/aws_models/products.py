"""DynamoDB operations for Products table."""

import uuid
from datetime import datetime
from botocore.exceptions import ClientError
from app.aws_config import products_table


def get_product_by_id(product_id):
    """Get a product by ID.
    
    Args:
        product_id: Product UUID
        
    Returns:
        dict: Product data or None
    """
    try:
        response = products_table.get_item(Key={'id': product_id})
        return response.get('Item')
    except ClientError as e:
        print(f"Error getting product: {e}")
        return None


def get_products_by_bakery(bakery_id):
    """Get all products for a bakery using GSI.
    
    Args:
        bakery_id: Bakery UUID
        
    Returns:
        list: List of products
    """
    try:
        response = products_table.query(
            IndexName='bakery_id-index',
            KeyConditionExpression='bakery_id = :bid',
            ExpressionAttributeValues={':bid': bakery_id}
        )
        return response.get('Items', [])
    except ClientError as e:
        print(f"Error querying products by bakery: {e}")
        # Fallback to scan
        try:
            response = products_table.scan(
                FilterExpression='bakery_id = :bid',
                ExpressionAttributeValues={':bid': bakery_id}
            )
            return response.get('Items', [])
        except:
            return []


def get_available_products(bakery_id):
    """Get available products for a bakery.
    
    Args:
        bakery_id: Bakery UUID
        
    Returns:
        list: List of available products
    """
    try:
        response = products_table.scan(
            FilterExpression='bakery_id = :bid AND is_available = :avail AND stock_quantity > :zero',
            ExpressionAttributeValues={
                ':bid': bakery_id,
                ':avail': True,
                ':zero': 0
            }
        )
        return response.get('Items', [])
    except ClientError as e:
        print(f"Error getting available products: {e}")
        return []


def create_product(bakery_id, name, price, description=None, ingredients=None,
                   category_id=None, discount_price=None, image_url='default-product.png',
                   stock_quantity=0, is_vegetarian=True, preparation_time_mins=15):
    """Create a new product.
    
    Args:
        bakery_id: Bakery UUID
        name: Product name
        price: Regular price
        description: Product description
        ingredients: Ingredients list
        category_id: Category UUID
        discount_price: Discounted price
        image_url: Product image filename
        stock_quantity: Initial stock
        is_vegetarian: Vegetarian flag
        preparation_time_mins: Preparation time
        
    Returns:
        dict: Created product data or None on error
    """
    try:
        product_id = str(uuid.uuid4())
        
        product_data = {
            'id': product_id,
            'bakery_id': bakery_id,
            'category_id': category_id or '',
            'name': name,
            'description': description or '',
            'ingredients': ingredients or '',
            'price': float(price),
            'discount_price': float(discount_price) if discount_price else None,
            'image_url': image_url,
            'stock_quantity': int(stock_quantity),
            'is_available': True,
            'is_vegetarian': bool(is_vegetarian),
            'is_bestseller': False,
            'preparation_time_mins': int(preparation_time_mins),
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        products_table.put_item(Item=product_data)
        return product_data
    except ClientError as e:
        print(f"Error creating product: {e}")
        return None


def update_product(product_id, updates):
    """Update product attributes.
    
    Args:
        product_id: Product UUID
        updates: Dictionary of attributes to update
        
    Returns:
        bool: True if successful
    """
    try:
        update_expr = "SET updated_at = :updated_at"
        expr_values = {':updated_at': datetime.utcnow().isoformat()}
        
        for key, value in updates.items():
            if key not in ['id', 'bakery_id']:  # Don't allow changing PK or bakery
                update_expr += f", {key} = :{key}"
                expr_values[f':{key}'] = value
        
        products_table.update_item(
            Key={'id': product_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values
        )
        return True
    except ClientError as e:
        print(f"Error updating product: {e}")
        return False


def delete_product(product_id):
    """Delete a product.
    
    Args:
        product_id: Product UUID
        
    Returns:
        bool: True if successful
    """
    try:
        products_table.delete_item(Key={'id': product_id})
        return True
    except ClientError as e:
        print(f"Error deleting product: {e}")
        return False


def reduce_stock(product_id, quantity):
    """Reduce product stock by quantity.
    
    Args:
        product_id: Product UUID
        quantity: Quantity to reduce
        
    Returns:
        bool: True if successful, False if insufficient stock
    """
    try:
        product = get_product_by_id(product_id)
        if not product:
            return False
        
        current_stock = product.get('stock_quantity', 0)
        if current_stock < quantity:
            return False
        
        new_stock = current_stock - quantity
        products_table.update_item(
            Key={'id': product_id},
            UpdateExpression="SET stock_quantity = :stock, updated_at = :updated",
            ExpressionAttributeValues={
                ':stock': new_stock,
                ':updated': datetime.utcnow().isoformat()
            }
        )
        return True
    except ClientError as e:
        print(f"Error reducing stock: {e}")
        return False


def add_stock(product_id, quantity):
    """Add to product stock.
    
    Args:
        product_id: Product UUID
        quantity: Quantity to add
        
    Returns:
        bool: True if successful
    """
    try:
        product = get_product_by_id(product_id)
        if not product:
            return False
        
        new_stock = product.get('stock_quantity', 0) + quantity
        return update_product(product_id, {'stock_quantity': new_stock})
    except ClientError as e:
        print(f"Error adding stock: {e}")
        return False


def get_bestsellers(bakery_id=None, limit=10):
    """Get bestseller products.
    
    Args:
        bakery_id: Optional - filter by bakery
        limit: Maximum number of results
        
    Returns:
        list: List of bestseller products
    """
    try:
        filter_expr = 'is_bestseller = :best AND is_available = :avail'
        expr_values = {':best': True, ':avail': True}
        
        if bakery_id:
            filter_expr += ' AND bakery_id = :bid'
            expr_values[':bid'] = bakery_id
        
        response = products_table.scan(
            FilterExpression=filter_expr,
            ExpressionAttributeValues=expr_values,
            Limit=limit
        )
        return response.get('Items', [])
    except ClientError as e:
        print(f"Error getting bestsellers: {e}")
        return []
