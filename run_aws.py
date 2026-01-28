"""AWS Application entry point for FreshBakes.

This entry point uses DynamoDB for data storage and SNS for notifications.
Use this for AWS EC2 deployment.

For local development with SQLite, use run.py instead.
"""

import os
from flask import Flask, render_template, session

# Set environment for AWS
os.environ.setdefault('FLASK_CONFIG', 'production')


def create_app_aws():
    """Create Flask application configured for AWS deployment."""
    app = Flask(__name__, 
                template_folder='app/templates',
                static_folder='app/static')
    
    # Load configuration
    app.secret_key = os.environ.get('SECRET_KEY', 'aws-secret-key-change-in-production')
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'app', 'static', 'images')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
    
    # Ensure upload directories exist
    upload_dirs = ['bakeries', 'products', 'profiles']
    for dir_name in upload_dirs:
        dir_path = os.path.join(app.config['UPLOAD_FOLDER'], dir_name)
        os.makedirs(dir_path, exist_ok=True)
    
    # Register AWS blueprints
    from app.routes_aws import register_aws_blueprints
    register_aws_blueprints(app)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500
    
    # Context processors
    @app.context_processor
    def inject_globals():
        """Inject global variables into templates."""
        from app.aws_models.cart import get_cart_total
        
        cart_count = 0
        current_user = None
        
        if 'user_email' in session:
            cart_data = get_cart_total(session['user_email'])
            cart_count = cart_data.get('item_count', 0)
            
            # Create a user-like dict for templates
            from app.aws_models.users import get_user_by_email
            current_user = get_user_by_email(session['user_email'])
        
        return dict(
            cart_count=cart_count,
            current_user=current_user
        )
    
    # Template filters
    @app.template_filter('currency')
    def currency_filter(value):
        """Format value as currency."""
        try:
            return f"${float(value):.2f}"
        except (ValueError, TypeError):
            return "$0.00"
    
    @app.template_filter('datetime')
    def datetime_filter(value, format='%b %d, %Y %I:%M %p'):
        """Format datetime string."""
        if not value:
            return ''
        try:
            from datetime import datetime
            if isinstance(value, str):
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            else:
                dt = value
            return dt.strftime(format)
        except:
            return str(value)
    
    return app


# Create the application
app = create_app_aws()

if __name__ == '__main__':
    # Run with host 0.0.0.0 for EC2 deployment
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    
    print(f"Starting FreshBakes AWS server on port {port}...")
    print("Using DynamoDB for data storage")
    print("Using SNS for notifications")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
