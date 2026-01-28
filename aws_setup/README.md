# FreshBakes AWS Deployment Guide

Complete guide for deploying FreshBakes to AWS using EC2, DynamoDB, and SNS.

## Prerequisites

- AWS Account with appropriate permissions
- AWS CLI installed and configured
- Python 3.9+ installed

---

## Step 1: IAM Role Setup

### Create IAM Role for EC2

1. Go to **IAM Console** → **Roles** → **Create Role**
2. Select **AWS Service** → **EC2** → Next
3. Add the following policies:
   - `AmazonDynamoDBFullAccess`
   - `AmazonSNSFullAccess`
4. Name the role: `FreshBakes-EC2-Role`
5. Create the role

### Or create custom policy (more secure):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem",
                "dynamodb:Query",
                "dynamodb:Scan",
                "dynamodb:CreateTable",
                "dynamodb:DescribeTable"
            ],
            "Resource": "arn:aws:dynamodb:*:*:table/FreshBakes_*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "sns:Publish"
            ],
            "Resource": "arn:aws:sns:*:*:FreshBakes-*"
        }
    ]
}
```

---

## Step 2: Create DynamoDB Tables

### Option A: Using the provided script

```bash
# From project root
cd d:\FreshBakes
python aws_setup/create_tables.py
```

### Option B: Manual creation via AWS Console

Create the following tables in **DynamoDB Console**:

| Table Name | Partition Key | Sort Key | GSIs |
|------------|---------------|----------|------|
| FreshBakes_Users | email (S) | - | role-index |
| FreshBakes_Bakeries | id (S) | - | owner_email-index |
| FreshBakes_Products | id (S) | - | bakery_id-index |
| FreshBakes_Categories | id (S) | - | bakery_id-index |
| FreshBakes_Orders | order_number (S) | - | customer_email-index, bakery_id-index |
| FreshBakes_CartItems | user_email (S) | product_id (S) | - |
| FreshBakes_Reviews | id (S) | - | bakery_id-index, order_id-index |
| FreshBakes_Addresses | id (S) | - | user_email-index |
| FreshBakes_Coupons | code (S) | - | bakery_id-index |

---

## Step 3: Create SNS Topic

1. Go to **SNS Console** → **Topics** → **Create Topic**
2. Type: **Standard**
3. Name: `FreshBakes-notifications`
4. Create topic
5. Copy the **Topic ARN** (e.g., `arn:aws:sns:us-east-1:123456789:FreshBakes-notifications`)

### Subscribe to the topic:

1. Click the topic → **Create subscription**
2. Protocol: **Email**
3. Endpoint: Your email address
4. Confirm the subscription via email

---

## Step 4: Launch EC2 Instance

1. Go to **EC2 Console** → **Launch Instance**
2. Configure:
   - **Name**: FreshBakes-Server
   - **AMI**: Amazon Linux 2023 or Ubuntu 22.04
   - **Instance type**: t2.micro (free tier) or t2.small
   - **Key pair**: Create or select existing
   - **Network settings**: Allow HTTP (80), HTTPS (443), SSH (22)
   - **IAM Role**: Select `FreshBakes-EC2-Role`
3. Launch instance

---

## Step 5: Deploy Application to EC2

### Connect to EC2:

```bash
ssh -i your-key.pem ec2-user@your-ec2-public-ip
```

### Install dependencies:

```bash
# Update system
sudo yum update -y  # Amazon Linux
# OR
sudo apt update && sudo apt upgrade -y  # Ubuntu

# Install Python
sudo yum install python3 python3-pip git -y  # Amazon Linux
# OR
sudo apt install python3 python3-pip git -y  # Ubuntu
```

### Clone and setup application:

```bash
# Clone your repository
git clone https://github.com/your-username/FreshBakes.git
cd FreshBakes

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Set environment variables:

```bash
# Create .env file or export variables
export AWS_REGION=us-east-1
export SNS_TOPIC_ARN=arn:aws:sns:us-east-1:YOUR_ACCOUNT:FreshBakes-notifications
export SECRET_KEY=your-super-secret-key-here
export FLASK_DEBUG=0
```

### Run the application:

```bash
# Test run
python run_aws.py

# Production with gunicorn
pip install gunicorn
gunicorn --bind 0.0.0.0:5000 run_aws:app
```

---

## Step 6: Setup Production Server (Optional)

### Install and configure Nginx:

```bash
sudo yum install nginx -y  # Amazon Linux
# OR
sudo apt install nginx -y  # Ubuntu

# Create Nginx config
sudo nano /etc/nginx/conf.d/freshbakes.conf
```

Add this configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        alias /home/ec2-user/FreshBakes/app/static;
    }
}
```

### Setup systemd service:

```bash
sudo nano /etc/systemd/system/freshbakes.service
```

Add:

```ini
[Unit]
Description=FreshBakes Flask Application
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/FreshBakes
Environment="PATH=/home/ec2-user/FreshBakes/venv/bin"
Environment="AWS_REGION=us-east-1"
Environment="SNS_TOPIC_ARN=arn:aws:sns:us-east-1:YOUR_ACCOUNT:FreshBakes-notifications"
Environment="SECRET_KEY=your-secret-key"
ExecStart=/home/ec2-user/FreshBakes/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 run_aws:app

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable freshbakes
sudo systemctl start freshbakes
sudo systemctl start nginx
```

---

## Step 7: Create Admin User

After deployment, create an admin user by running:

```bash
python -c "
from app.aws_models.users import create_user
user = create_user('admin@freshbakes.com', 'YourSecurePassword123', 'Admin User', '', 'admin')
print('Admin created:', user['email'] if user else 'Failed')
"
```

---

## Environment Variables Reference

| Variable | Description | Required |
|----------|-------------|----------|
| `AWS_REGION` | AWS region (e.g., us-east-1) | Yes |
| `SNS_TOPIC_ARN` | Full ARN of SNS topic | Yes |
| `SECRET_KEY` | Flask secret key for sessions | Yes |
| `FLASK_DEBUG` | Set to 0 for production | Recommended |
| `PORT` | Application port (default: 5000) | No |

---

## Troubleshooting

### Check application logs:

```bash
sudo journalctl -u freshbakes -f
```

### Test DynamoDB connection:

```bash
python -c "
import boto3
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
tables = list(dynamodb.tables.all())
print('Tables:', [t.name for t in tables])
"
```

### Test SNS:

```bash
python -c "
import boto3
sns = boto3.client('sns', region_name='us-east-1')
response = sns.publish(
    TopicArn='YOUR_TOPIC_ARN',
    Subject='Test',
    Message='Test message from FreshBakes'
)
print('Message ID:', response['MessageId'])
"
```

---

## Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Use HTTPS (configure SSL certificate)
- [ ] Restrict IAM permissions to minimum required
- [ ] Enable DynamoDB encryption at rest
- [ ] Configure security groups properly
- [ ] Set up CloudWatch monitoring
- [ ] Enable VPC for EC2 instance
