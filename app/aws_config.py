"""AWS Configuration and boto3 clients."""

import os
import boto3
from botocore.exceptions import ClientError

# AWS Region Configuration
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Initialize boto3 clients
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
sns = boto3.client('sns', region_name=AWS_REGION)

# DynamoDB Table References
users_table = dynamodb.Table('FreshBakes_Users')
bakeries_table = dynamodb.Table('FreshBakes_Bakeries')
categories_table = dynamodb.Table('FreshBakes_Categories')
products_table = dynamodb.Table('FreshBakes_Products')
orders_table = dynamodb.Table('FreshBakes_Orders')
cart_table = dynamodb.Table('FreshBakes_CartItems')
reviews_table = dynamodb.Table('FreshBakes_Reviews')
addresses_table = dynamodb.Table('FreshBakes_Addresses')
coupons_table = dynamodb.Table('FreshBakes_Coupons')

# SNS Topic ARN (Replace with your actual SNS Topic ARN after creation)
SNS_TOPIC_ARN = os.environ.get(
    'SNS_TOPIC_ARN', 
    'arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:FreshBakes-notifications'
)


def send_notification(subject, message):
    """Send a notification via SNS.
    
    Args:
        subject: Notification subject (max 100 chars)
        message: Notification message body
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        response = sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject[:100],  # SNS subject limit
            Message=message
        )
        print(f"SNS notification sent: {response.get('MessageId')}")
        return True
    except ClientError as e:
        print(f"Error sending SNS notification: {e}")
        return False


def get_table(table_name):
    """Get a DynamoDB table reference by name.
    
    Args:
        table_name: Name of the table
        
    Returns:
        DynamoDB Table resource
    """
    return dynamodb.Table(f'FreshBakes_{table_name}')
