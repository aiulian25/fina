from app import db
from datetime import datetime
from sqlalchemy import func

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    frequency = db.Column(db.String(20), nullable=False)  # monthly, weekly, yearly, quarterly, custom
    custom_interval_days = db.Column(db.Integer, nullable=True)  # For custom frequency
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    next_due_date = db.Column(db.Date, nullable=True)
    start_date = db.Column(db.Date, nullable=True)  # First occurrence date
    end_date = db.Column(db.Date, nullable=True)  # Optional end date
    total_occurrences = db.Column(db.Integer, nullable=True)  # Optional limit
    occurrences_count = db.Column(db.Integer, default=0)  # Current count
    is_active = db.Column(db.Boolean, default=True)
    is_confirmed = db.Column(db.Boolean, default=False)  # User confirmed this subscription
    auto_detected = db.Column(db.Boolean, default=False)  # System detected this pattern
    auto_create_expense = db.Column(db.Boolean, default=False)  # Auto-create expenses on due date
    confidence_score = db.Column(db.Float, default=0.0)  # 0-100 confidence of detection
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_reminded = db.Column(db.DateTime, nullable=True)
    last_auto_created = db.Column(db.Date, nullable=True)  # Last auto-created expense date
    
    def __repr__(self):
        return f'<Subscription {self.name}>'
    
    def get_frequency_days(self):
        """Get number of days between payments"""
        if self.frequency == 'custom' and self.custom_interval_days:
            return self.custom_interval_days
        
        frequency_map = {
            'weekly': 7,
            'biweekly': 14,
            'monthly': 30,
            'quarterly': 90,
            'yearly': 365
        }
        return frequency_map.get(self.frequency, 30)
    
    def should_create_expense_today(self):
        """Check if an expense should be auto-created today"""
        if not self.auto_create_expense or not self.is_active:
            return False
        
        if not self.next_due_date:
            return False
        
        today = datetime.now().date()
        
        # Check if today is the due date
        if self.next_due_date != today:
            return False
        
        # Check if already created today
        if self.last_auto_created == today:
            return False
        
        # Check if we've reached the occurrence limit
        if self.total_occurrences and self.occurrences_count >= self.total_occurrences:
            return False
        
        # Check if past end date
        if self.end_date and today > self.end_date:
            return False
        
        return True
    
    def advance_next_due_date(self):
        """Move to the next due date"""
        if not self.next_due_date:
            return
        
        from datetime import timedelta
        interval_days = self.get_frequency_days()
        self.next_due_date = self.next_due_date + timedelta(days=interval_days)
        self.occurrences_count += 1
        
        # Check if subscription should end
        if self.total_occurrences and self.occurrences_count >= self.total_occurrences:
            self.is_active = False
        
        if self.end_date and self.next_due_date > self.end_date:
            self.is_active = False
    
    def get_annual_cost(self):
        """Calculate annual cost based on frequency"""
        frequency_multiplier = {
            'weekly': 52,
            'biweekly': 26,
            'monthly': 12,
            'quarterly': 4,
            'yearly': 1
        }
        return self.amount * frequency_multiplier.get(self.frequency, 12)


class RecurringPattern(db.Model):
    """Detected recurring patterns (suggestions before confirmation)"""
    __tablename__ = 'recurring_patterns'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    suggested_name = db.Column(db.String(100), nullable=False)
    average_amount = db.Column(db.Float, nullable=False)
    detected_frequency = db.Column(db.String(20), nullable=False)
    confidence_score = db.Column(db.Float, nullable=False)  # 0-100
    expense_ids = db.Column(db.Text, nullable=False)  # JSON array of expense IDs
    first_occurrence = db.Column(db.Date, nullable=False)
    last_occurrence = db.Column(db.Date, nullable=False)
    occurrence_count = db.Column(db.Integer, default=0)
    is_dismissed = db.Column(db.Boolean, default=False)
    is_converted = db.Column(db.Boolean, default=False)  # Converted to subscription
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<RecurringPattern {self.suggested_name}>'
