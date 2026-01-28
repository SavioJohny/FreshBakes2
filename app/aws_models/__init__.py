"""AWS DynamoDB Models Package.

This package provides DynamoDB operations for all FreshBakes entities.
"""

from .users import (
    get_user_by_email,
    create_user,
    verify_password,
    update_user,
    get_all_users,
    get_users_by_role
)

from .bakeries import (
    get_bakery_by_id,
    get_bakery_by_owner,
    create_bakery,
    update_bakery,
    get_all_bakeries,
    get_approved_bakeries,
    get_featured_bakeries
)

from .products import (
    get_product_by_id,
    get_products_by_bakery,
    create_product,
    update_product,
    delete_product,
    get_available_products
)

from .orders import (
    create_order,
    get_order_by_number,
    get_orders_by_customer,
    get_orders_by_bakery,
    update_order_status,
    get_all_orders
)

from .cart import (
    get_cart_items,
    add_to_cart,
    update_cart_item,
    remove_from_cart,
    clear_cart
)

from .reviews import (
    create_review,
    get_reviews_by_bakery,
    get_reviews_by_product,
    get_review_by_id
)

from .notifications import (
    send_sns_notification,
    notify_new_order,
    notify_order_status_change,
    notify_new_user_signup,
    notify_bakery_approved
)

from .categories import (
    get_category_by_id,
    get_categories_by_bakery,
    create_category,
    update_category,
    delete_category
)

__all__ = [
    # Users
    'get_user_by_email', 'create_user', 'verify_password', 
    'update_user', 'get_all_users', 'get_users_by_role',
    # Bakeries
    'get_bakery_by_id', 'get_bakery_by_owner', 'create_bakery',
    'update_bakery', 'get_all_bakeries', 'get_approved_bakeries',
    'get_featured_bakeries',
    # Products
    'get_product_by_id', 'get_products_by_bakery', 'create_product',
    'update_product', 'delete_product', 'get_available_products',
    # Orders
    'create_order', 'get_order_by_number', 'get_orders_by_customer',
    'get_orders_by_bakery', 'update_order_status', 'get_all_orders',
    # Cart
    'get_cart_items', 'add_to_cart', 'update_cart_item',
    'remove_from_cart', 'clear_cart',
    # Reviews
    'create_review', 'get_reviews_by_bakery', 'get_reviews_by_product',
    'get_review_by_id',
    # Notifications
    'send_sns_notification', 'notify_new_order', 'notify_order_status_change',
    'notify_new_user_signup', 'notify_bakery_approved',
    # Categories
    'get_category_by_id', 'get_categories_by_bakery', 'create_category',
    'update_category', 'delete_category',
]
