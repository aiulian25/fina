#!/usr/bin/env python3
"""
Test script to create backdated recurring income entries
This will test the automatic income creation feature
"""
from datetime import datetime, timedelta
from app import create_app, db
from app.models import Income, User
from app.routes.income import calculate_income_next_due_date

def create_test_income():
    """Create backdated recurring income for testing"""
    app = create_app()
    
    with app.app_context():
        # Get the first user (or create test user)
        user = User.query.first()
        if not user:
            print("No users found in database. Please create a user first.")
            return
        
        print(f"Creating test income for user: {user.username}")
        print(f"User currency: {user.currency}")
        
        # Test 1: Monthly salary - backdated 2 months (should trigger 2 auto-creations)
        two_months_ago = datetime.utcnow() - timedelta(days=60)
        next_due_date = calculate_income_next_due_date('monthly', None, two_months_ago)
        
        salary_income = Income(
            amount=5000.0,
            currency=user.currency,
            description="Monthly Salary - Test",
            source="Salary",
            user_id=user.id,
            tags='["recurring", "salary", "test"]',
            frequency='monthly',
            next_due_date=next_due_date,
            is_active=True,
            auto_create=True,
            date=two_months_ago
        )
        db.session.add(salary_income)
        print(f"✓ Created monthly salary income backdated to {two_months_ago.date()}")
        print(f"  Next due date: {next_due_date.date() if next_due_date else 'None'}")
        
        # Test 2: Biweekly freelance - backdated 4 weeks (should trigger 2 auto-creations)
        four_weeks_ago = datetime.utcnow() - timedelta(days=28)
        next_due_date = calculate_income_next_due_date('biweekly', None, four_weeks_ago)
        
        freelance_income = Income(
            amount=1500.0,
            currency=user.currency,
            description="Freelance Project - Test",
            source="Freelance",
            user_id=user.id,
            tags='["recurring", "freelance", "test"]',
            frequency='biweekly',
            next_due_date=next_due_date,
            is_active=True,
            auto_create=True,
            date=four_weeks_ago
        )
        db.session.add(freelance_income)
        print(f"✓ Created biweekly freelance income backdated to {four_weeks_ago.date()}")
        print(f"  Next due date: {next_due_date.date() if next_due_date else 'None'}")
        
        # Test 3: Weekly side gig - backdated 3 weeks (should trigger 3 auto-creations)
        three_weeks_ago = datetime.utcnow() - timedelta(days=21)
        next_due_date = calculate_income_next_due_date('weekly', None, three_weeks_ago)
        
        weekly_income = Income(
            amount=300.0,
            currency=user.currency,
            description="Side Gig - Test",
            source="Freelance",
            user_id=user.id,
            tags='["recurring", "side-gig", "test"]',
            frequency='weekly',
            next_due_date=next_due_date,
            is_active=True,
            auto_create=True,
            date=three_weeks_ago
        )
        db.session.add(weekly_income)
        print(f"✓ Created weekly side gig income backdated to {three_weeks_ago.date()}")
        print(f"  Next due date: {next_due_date.date() if next_due_date else 'None'}")
        
        # Test 4: Every 4 weeks contract - backdated 8 weeks (should trigger 2 auto-creations)
        eight_weeks_ago = datetime.utcnow() - timedelta(days=56)
        next_due_date = calculate_income_next_due_date('every4weeks', None, eight_weeks_ago)
        
        contract_income = Income(
            amount=2000.0,
            currency=user.currency,
            description="Contract Work - Test",
            source="Freelance",
            user_id=user.id,
            tags='["recurring", "contract", "test"]',
            frequency='every4weeks',
            next_due_date=next_due_date,
            is_active=True,
            auto_create=True,
            date=eight_weeks_ago
        )
        db.session.add(contract_income)
        print(f"✓ Created every-4-weeks contract income backdated to {eight_weeks_ago.date()}")
        print(f"  Next due date: {next_due_date.date() if next_due_date else 'None'}")
        
        # Test 5: Custom 10-day cycle - backdated 30 days (should trigger 3 auto-creations)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        next_due_date = calculate_income_next_due_date('custom', 10, thirty_days_ago)
        
        custom_income = Income(
            amount=500.0,
            currency=user.currency,
            description="Custom Cycle Income - Test",
            source="Other",
            user_id=user.id,
            tags='["recurring", "custom", "test"]',
            frequency='custom',
            custom_days=10,
            next_due_date=next_due_date,
            is_active=True,
            auto_create=True,
            date=thirty_days_ago
        )
        db.session.add(custom_income)
        print(f"✓ Created custom (10-day) income backdated to {thirty_days_ago.date()}")
        print(f"  Next due date: {next_due_date.date() if next_due_date else 'None'}")
        
        db.session.commit()
        
        print("\n" + "="*60)
        print("✓ Test recurring income entries created successfully!")
        print("="*60)
        print("\nExpected auto-creations when scheduler runs:")
        print("- Monthly Salary: ~2 entries")
        print("- Biweekly Freelance: ~2 entries")
        print("- Weekly Side Gig: ~3 entries")
        print("- Every-4-weeks Contract: ~2 entries")
        print("- Custom 10-day: ~3 entries")
        print("\nTotal expected: ~12 auto-created income entries")
        print("\nTo trigger scheduler manually, run:")
        print("docker compose exec web python -c \"from app.scheduler import process_due_recurring_income; process_due_recurring_income()\"")

if __name__ == '__main__':
    create_test_income()
