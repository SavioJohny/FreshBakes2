"""DynamoDB Table Creation Script for FreshBakes.

Run this script to create all required DynamoDB tables in your AWS account.
Make sure you have:
1. AWS credentials configured (~/.aws/credentials or environment variables)
2. boto3 installed (pip install boto3)

Usage:
    python aws_setup/create_tables.py

Note: Tables take a few seconds to become ACTIVE after creation.
"""

import boto3
import time
import sys

# AWS Region (change if needed)
REGION = 'us-east-1'

# Table prefix
PREFIX = 'FreshBakes_'

# Initialize DynamoDB client
dynamodb = boto3.client('dynamodb', region_name=REGION)


def wait_for_table(table_name):
    """Wait for a table to become ACTIVE."""
    print(f"  Waiting for {table_name} to become ACTIVE...")
    waiter = dynamodb.get_waiter('table_exists')
    waiter.wait(TableName=table_name)
    print(f"  {table_name} is now ACTIVE")


def create_users_table():
    """Create Users table."""
    table_name = f'{PREFIX}Users'
    print(f"Creating {table_name}...")
    
    try:
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'email', 'KeyType': 'HASH'}  # Partition key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'email', 'AttributeType': 'S'},
                {'AttributeName': 'role', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'role-index',
                    'KeySchema': [
                        {'AttributeName': 'role', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        wait_for_table(table_name)
    except dynamodb.exceptions.ResourceInUseException:
        print(f"  {table_name} already exists, skipping...")


def create_bakeries_table():
    """Create Bakeries table."""
    table_name = f'{PREFIX}Bakeries'
    print(f"Creating {table_name}...")
    
    try:
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'id', 'AttributeType': 'S'},
                {'AttributeName': 'owner_email', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'owner_email-index',
                    'KeySchema': [
                        {'AttributeName': 'owner_email', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        wait_for_table(table_name)
    except dynamodb.exceptions.ResourceInUseException:
        print(f"  {table_name} already exists, skipping...")


def create_products_table():
    """Create Products table."""
    table_name = f'{PREFIX}Products'
    print(f"Creating {table_name}...")
    
    try:
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'id', 'AttributeType': 'S'},
                {'AttributeName': 'bakery_id', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'bakery_id-index',
                    'KeySchema': [
                        {'AttributeName': 'bakery_id', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        wait_for_table(table_name)
    except dynamodb.exceptions.ResourceInUseException:
        print(f"  {table_name} already exists, skipping...")


def create_categories_table():
    """Create Categories table."""
    table_name = f'{PREFIX}Categories'
    print(f"Creating {table_name}...")
    
    try:
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'id', 'AttributeType': 'S'},
                {'AttributeName': 'bakery_id', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'bakery_id-index',
                    'KeySchema': [
                        {'AttributeName': 'bakery_id', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        wait_for_table(table_name)
    except dynamodb.exceptions.ResourceInUseException:
        print(f"  {table_name} already exists, skipping...")


def create_orders_table():
    """Create Orders table."""
    table_name = f'{PREFIX}Orders'
    print(f"Creating {table_name}...")
    
    try:
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'order_number', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'order_number', 'AttributeType': 'S'},
                {'AttributeName': 'customer_email', 'AttributeType': 'S'},
                {'AttributeName': 'bakery_id', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'customer_email-index',
                    'KeySchema': [
                        {'AttributeName': 'customer_email', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                },
                {
                    'IndexName': 'bakery_id-index',
                    'KeySchema': [
                        {'AttributeName': 'bakery_id', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        wait_for_table(table_name)
    except dynamodb.exceptions.ResourceInUseException:
        print(f"  {table_name} already exists, skipping...")


def create_cart_table():
    """Create CartItems table with composite key."""
    table_name = f'{PREFIX}CartItems'
    print(f"Creating {table_name}...")
    
    try:
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'user_email', 'KeyType': 'HASH'},  # Partition key
                {'AttributeName': 'product_id', 'KeyType': 'RANGE'}  # Sort key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_email', 'AttributeType': 'S'},
                {'AttributeName': 'product_id', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        wait_for_table(table_name)
    except dynamodb.exceptions.ResourceInUseException:
        print(f"  {table_name} already exists, skipping...")


def create_reviews_table():
    """Create Reviews table."""
    table_name = f'{PREFIX}Reviews'
    print(f"Creating {table_name}...")
    
    try:
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'id', 'AttributeType': 'S'},
                {'AttributeName': 'bakery_id', 'AttributeType': 'S'},
                {'AttributeName': 'order_number', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'bakery_id-index',
                    'KeySchema': [
                        {'AttributeName': 'bakery_id', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                },
                {
                    'IndexName': 'order_id-index',
                    'KeySchema': [
                        {'AttributeName': 'order_number', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        wait_for_table(table_name)
    except dynamodb.exceptions.ResourceInUseException:
        print(f"  {table_name} already exists, skipping...")


def create_addresses_table():
    """Create Addresses table."""
    table_name = f'{PREFIX}Addresses'
    print(f"Creating {table_name}...")
    
    try:
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'id', 'AttributeType': 'S'},
                {'AttributeName': 'user_email', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'user_email-index',
                    'KeySchema': [
                        {'AttributeName': 'user_email', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        wait_for_table(table_name)
    except dynamodb.exceptions.ResourceInUseException:
        print(f"  {table_name} already exists, skipping...")


def create_coupons_table():
    """Create Coupons table."""
    table_name = f'{PREFIX}Coupons'
    print(f"Creating {table_name}...")
    
    try:
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'code', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'code', 'AttributeType': 'S'},
                {'AttributeName': 'bakery_id', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'bakery_id-index',
                    'KeySchema': [
                        {'AttributeName': 'bakery_id', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        wait_for_table(table_name)
    except dynamodb.exceptions.ResourceInUseException:
        print(f"  {table_name} already exists, skipping...")


def create_all_tables():
    """Create all DynamoDB tables for FreshBakes."""
    print("=" * 50)
    print("FreshBakes DynamoDB Table Creation")
    print(f"Region: {REGION}")
    print("=" * 50)
    print()
    
    tables = [
        ('Users', create_users_table),
        ('Bakeries', create_bakeries_table),
        ('Products', create_products_table),
        ('Categories', create_categories_table),
        ('Orders', create_orders_table),
        ('CartItems', create_cart_table),
        ('Reviews', create_reviews_table),
        ('Addresses', create_addresses_table),
        ('Coupons', create_coupons_table),
    ]
    
    for name, create_func in tables:
        try:
            create_func()
            print()
        except Exception as e:
            print(f"  ERROR creating {name}: {e}")
            print()
    
    print("=" * 50)
    print("Table creation complete!")
    print()
    print("Created tables:")
    
    response = dynamodb.list_tables()
    for table in response['TableNames']:
        if table.startswith(PREFIX):
            print(f"  - {table}")
    
    print()
    print("You can now run the FreshBakes application with:")
    print("  python run_aws.py")
    print("=" * 50)


def delete_all_tables():
    """Delete all FreshBakes DynamoDB tables (use with caution!)."""
    print("WARNING: This will delete ALL FreshBakes tables!")
    confirm = input("Type 'DELETE' to confirm: ")
    
    if confirm != 'DELETE':
        print("Aborted.")
        return
    
    response = dynamodb.list_tables()
    for table in response['TableNames']:
        if table.startswith(PREFIX):
            print(f"Deleting {table}...")
            dynamodb.delete_table(TableName=table)
    
    print("All tables deleted.")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--delete':
        delete_all_tables()
    else:
        create_all_tables()
