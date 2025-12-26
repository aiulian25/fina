from app import create_app, db
from app.models import Income, User
from datetime import datetime
import json

app = create_app()
with app.app_context():
    # Get first user
    user = User.query.first()
    print(f"User found: {user.username if user else 'None'}, ID: {user.id if user else 'N/A'}")
    
    if user:
        # Create test income
        income = Income(
            amount=1000.0,
            currency='USD',
            description='Test Income',
            source='Salary',
            user_id=user.id,
            tags=json.dumps(['test']),
            frequency='once',
            date=datetime.utcnow()
        )
        db.session.add(income)
        db.session.commit()
        print(f"Income created with ID: {income.id}")
        
        # Verify it was saved
        saved_income = Income.query.filter_by(user_id=user.id).all()
        print(f"Total income entries for user: {len(saved_income)}")
        for inc in saved_income:
            print(f"  - {inc.description}: ${inc.amount}")
