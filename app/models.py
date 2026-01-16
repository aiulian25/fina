from app import db
from flask_login import UserMixin
from datetime import datetime, timedelta
import json

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    totp_secret = db.Column(db.String(32), nullable=True)
    two_factor_enabled = db.Column(db.Boolean, default=False)
    backup_codes = db.Column(db.Text, nullable=True)  # JSON array of hashed backup codes
    language = db.Column(db.String(5), default='en')
    currency = db.Column(db.String(3), default='USD')
    theme = db.Column(db.String(10), default='dark')  # 'light' or 'dark'
    notifications_enabled = db.Column(db.Boolean, default=True)  # Budget notifications
    avatar = db.Column(db.String(255), default='icons/avatars/avatar-1.svg')
    monthly_budget = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Account lockout fields for security
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    last_failed_login = db.Column(db.DateTime, nullable=True)
    
    # Security notification preferences
    security_notifications = db.Column(db.Boolean, default=True)  # New login alerts, etc.
    
    expenses = db.relationship('Expense', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    income = db.relationship('Income', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    categories = db.relationship('Category', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    documents = db.relationship('Document', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    recurring_expenses = db.relationship('RecurringExpense', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    # Account lockout constants
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION = timedelta(minutes=15)
    
    def is_locked(self):
        """Check if the account is currently locked"""
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False
    
    def get_lockout_remaining_minutes(self):
        """Get remaining lockout time in minutes"""
        if self.is_locked():
            remaining = (self.locked_until - datetime.utcnow()).seconds // 60
            return max(1, remaining)  # At least 1 minute
        return 0
    
    def record_failed_login(self):
        """Record a failed login attempt and lock account if needed"""
        self.failed_login_attempts = (self.failed_login_attempts or 0) + 1
        self.last_failed_login = datetime.utcnow()
        
        if self.failed_login_attempts >= self.MAX_FAILED_ATTEMPTS:
            self.locked_until = datetime.utcnow() + self.LOCKOUT_DURATION
        
        db.session.commit()
    
    def reset_failed_attempts(self):
        """Reset failed login attempts after successful login"""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_failed_login = None
        db.session.commit()
    
    def __repr__(self):
        return f'<User {self.username}>'


class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(7), default='#2b8cee')
    icon = db.Column(db.String(50), default='category')
    display_order = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Budget tracking fields
    monthly_budget = db.Column(db.Float, nullable=True)  # Monthly spending limit for this category
    budget_alert_threshold = db.Column(db.Float, default=0.9)  # Alert at 90% by default (0.0-2.0 range)
    
    expenses = db.relationship('Expense', backref='category', lazy='dynamic')
    
    def get_current_month_spending(self):
        """Calculate total spending for current month in this category"""
        from datetime import datetime
        now = datetime.utcnow()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        total = db.session.query(db.func.sum(Expense.amount)).filter(
            Expense.category_id == self.id,
            Expense.date >= start_of_month
        ).scalar()
        
        return float(total) if total else 0.0
    
    def get_budget_status(self):
        """Get budget status with spent amount, percentage, and alert status"""
        spent = self.get_current_month_spending()
        
        if not self.monthly_budget or self.monthly_budget <= 0:
            return {
                'spent': spent,
                'budget': 0,
                'remaining': 0,
                'percentage': 0,
                'alert_level': 'none'  # none, warning, danger, exceeded
            }
        
        percentage = (spent / self.monthly_budget) * 100
        remaining = self.monthly_budget - spent
        
        # Determine alert level
        alert_level = 'none'
        if percentage >= 100:
            alert_level = 'exceeded'
        elif percentage >= (self.budget_alert_threshold * 100):
            alert_level = 'danger'
        elif percentage >= ((self.budget_alert_threshold - 0.1) * 100):
            alert_level = 'warning'
        
        return {
            'spent': spent,
            'budget': self.monthly_budget,
            'remaining': remaining,
            'percentage': round(percentage, 1),
            'alert_level': alert_level
        }
    
    def __repr__(self):
        return f'<Category {self.name}>'
    
    def to_dict(self):
        budget_status = self.get_budget_status() if hasattr(self, 'get_budget_status') else None
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'icon': self.icon,
            'display_order': self.display_order,
            'created_at': self.created_at.isoformat(),
            'monthly_budget': self.monthly_budget,
            'budget_alert_threshold': self.budget_alert_threshold,
            'budget_status': budget_status
        }


class Expense(db.Model):
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD')
    description = db.Column(db.String(200), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tags = db.Column(db.Text, default='[]')  # JSON array of tags
    receipt_path = db.Column(db.String(255), nullable=True)
    receipt_ocr_text = db.Column(db.Text, nullable=True)  # Extracted text from receipt OCR for searchability
    date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Expense {self.description} - {self.amount} {self.currency}>'
    
    def get_tags(self):
        """Get tag names from the JSON tags column (legacy support)"""
        try:
            return json.loads(self.tags)
        except:
            return []
    
    def set_tags(self, tags_list):
        """Set tags in the JSON column (legacy support)"""
        self.tags = json.dumps(tags_list)
    
    def get_tag_objects(self):
        """Get Tag objects associated with this expense"""
        return self.tag_objects
    
    def add_tag(self, tag):
        """Add a tag to this expense"""
        if tag not in self.tag_objects:
            self.tag_objects.append(tag)
            tag.use_count += 1
    
    def remove_tag(self, tag):
        """Remove a tag from this expense"""
        if tag in self.tag_objects:
            self.tag_objects.remove(tag)
            if tag.use_count > 0:
                tag.use_count -= 1
    
    def to_dict(self):
        # Get tag objects with details
        tag_list = [tag.to_dict() for tag in self.get_tag_objects()]
        
        return {
            'id': self.id,
            'amount': self.amount,
            'currency': self.currency,
            'description': self.description,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'category_color': self.category.color if self.category else None,
            'tags': self.get_tags(),  # Legacy JSON tags
            'tag_objects': tag_list,  # New Tag objects
            'receipt_path': f'/uploads/{self.receipt_path}' if self.receipt_path else None,
            'date': self.date.isoformat(),
            'created_at': self.created_at.isoformat()
        }


class Document(db.Model):
    """
    Model for storing user documents (bank statements, receipts, invoices, etc.)
    Security: All queries filtered by user_id to ensure users only see their own documents
    """
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # in bytes
    file_type = db.Column(db.String(50), nullable=False)  # PDF, CSV, XLSX, etc.
    mime_type = db.Column(db.String(100), nullable=False)
    document_category = db.Column(db.String(100), nullable=True)  # Bank Statement, Invoice, Receipt, Contract, etc.
    status = db.Column(db.String(50), default='uploaded')  # uploaded, processing, analyzed, error
    ocr_text = db.Column(db.Text, nullable=True)  # Extracted text from OCR for searchability
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Document {self.filename} - {self.user_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.original_filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'mime_type': self.mime_type,
            'document_category': self.document_category,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class RecurringExpense(db.Model):
    """
    Model for storing recurring expenses (subscriptions, monthly bills, etc.)
    Security: All queries filtered by user_id to ensure users only see their own recurring expenses
    """
    __tablename__ = 'recurring_expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD')
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    frequency = db.Column(db.String(20), nullable=False)  # daily, weekly, monthly, yearly
    day_of_period = db.Column(db.Integer, nullable=True)  # day of month (1-31) or day of week (0-6)
    next_due_date = db.Column(db.DateTime, nullable=False)
    last_created_date = db.Column(db.DateTime, nullable=True)
    auto_create = db.Column(db.Boolean, default=False)  # Automatically create expense on due date
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text, nullable=True)
    detected = db.Column(db.Boolean, default=False)  # True if auto-detected, False if manually created
    confidence_score = db.Column(db.Float, default=0.0)  # 0-100, for auto-detected patterns
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Subscription-specific fields
    is_subscription = db.Column(db.Boolean, default=False)  # True if this is a subscription service
    service_name = db.Column(db.String(100), nullable=True)  # Normalized service name (netflix, spotify, etc.)
    last_used_date = db.Column(db.DateTime, nullable=True)  # When user last used this service
    reminder_days = db.Column(db.Integer, default=3)  # Days before renewal to send reminder
    reminder_sent = db.Column(db.Boolean, default=False)  # Whether reminder was sent for current cycle
    
    category = db.relationship('Category', backref='recurring_expenses')
    
    def __repr__(self):
        return f'<RecurringExpense {self.name} - {self.amount} {self.currency}>'
    
    def get_monthly_cost(self):
        """Calculate monthly cost based on frequency"""
        if self.frequency == 'daily':
            return self.amount * 30
        elif self.frequency == 'weekly':
            return self.amount * 4.33
        elif self.frequency == 'monthly':
            return self.amount
        elif self.frequency == 'yearly':
            return self.amount / 12
        return self.amount
    
    def get_yearly_cost(self):
        """Calculate yearly cost based on frequency"""
        if self.frequency == 'daily':
            return self.amount * 365
        elif self.frequency == 'weekly':
            return self.amount * 52
        elif self.frequency == 'monthly':
            return self.amount * 12
        elif self.frequency == 'yearly':
            return self.amount
        return self.amount * 12
    
    def days_until_renewal(self):
        """Calculate days until next renewal"""
        if not self.next_due_date:
            return None
        delta = self.next_due_date - datetime.utcnow()
        return delta.days
    
    def is_unused(self, days_threshold=60):
        """Check if subscription appears unused (not marked as used recently)"""
        if not self.last_used_date:
            # If never marked as used, consider unused after 60 days from creation
            days_since_creation = (datetime.utcnow() - self.created_at).days
            return days_since_creation > days_threshold
        days_since_use = (datetime.utcnow() - self.last_used_date).days
        return days_since_use > days_threshold
    
    def needs_reminder(self):
        """Check if subscription needs a renewal reminder"""
        if not self.is_active or self.reminder_sent:
            return False
        days = self.days_until_renewal()
        if days is None:
            return False
        return 0 <= days <= self.reminder_days
    
    def to_dict(self):
        days_until = self.days_until_renewal()
        return {
            'id': self.id,
            'name': self.name,
            'amount': self.amount,
            'currency': self.currency,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'category_color': self.category.color if self.category else None,
            'frequency': self.frequency,
            'day_of_period': self.day_of_period,
            'next_due_date': self.next_due_date.isoformat(),
            'last_created_date': self.last_created_date.isoformat() if self.last_created_date else None,
            'auto_create': self.auto_create,
            'is_active': self.is_active,
            'notes': self.notes,
            'detected': self.detected,
            'confidence_score': self.confidence_score,
            'is_subscription': self.is_subscription,
            'service_name': self.service_name,
            'last_used_date': self.last_used_date.isoformat() if self.last_used_date else None,
            'reminder_days': self.reminder_days,
            'reminder_sent': self.reminder_sent,
            'monthly_cost': round(self.get_monthly_cost(), 2),
            'yearly_cost': round(self.get_yearly_cost(), 2),
            'days_until_renewal': days_until,
            'is_unused': self.is_unused() if self.is_subscription else False,
            'needs_reminder': self.needs_reminder(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class Income(db.Model):
    """
    Model for storing user income (salary, freelance, investments, etc.)
    Security: All queries filtered by user_id to ensure users only see their own income
    """
    __tablename__ = 'income'
    
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    source = db.Column(db.String(100), nullable=False)  # Salary, Freelance, Investment, Rental, Gift, Other
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tags = db.Column(db.Text, default='[]')  # JSON array of tags
    frequency = db.Column(db.String(50), default='once')  # once, weekly, biweekly, every4weeks, monthly, custom
    custom_days = db.Column(db.Integer, nullable=True)  # For custom frequency
    next_due_date = db.Column(db.DateTime, nullable=True)  # Next date when recurring income is due
    last_created_date = db.Column(db.DateTime, nullable=True)  # Last date when income was auto-created
    is_active = db.Column(db.Boolean, default=True)  # Whether recurring income is active
    auto_create = db.Column(db.Boolean, default=False)  # Automatically create income entries
    date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Income {self.description} - {self.amount} {self.currency}>'
    
    def get_frequency_days(self):
        """Calculate days until next occurrence based on frequency"""
        if self.frequency == 'custom' and self.custom_days:
            return self.custom_days
        
        frequency_map = {
            'once': 0,  # One-time income
            'weekly': 7,
            'biweekly': 14,
            'every4weeks': 28,
            'monthly': 30,
        }
        return frequency_map.get(self.frequency, 0)
    
    def is_recurring(self):
        """Check if this income is recurring"""
        return self.frequency != 'once' and self.is_active
    
    def get_tags(self):
        try:
            return json.loads(self.tags)
        except:
            return []
    
    def set_tags(self, tags_list):
        self.tags = json.dumps(tags_list)
    
    def to_dict(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'currency': self.currency,
            'description': self.description,
            'source': self.source,
            'tags': self.get_tags(),
            'frequency': self.frequency,
            'custom_days': self.custom_days,
            'next_due_date': self.next_due_date.isoformat() if self.next_due_date else None,
            'last_created_date': self.last_created_date.isoformat() if self.last_created_date else None,
            'is_active': self.is_active,
            'auto_create': self.auto_create,
            'is_recurring': self.is_recurring(),
            'frequency_days': self.get_frequency_days(),
            'date': self.date.isoformat(),
            'created_at': self.created_at.isoformat()
        }


class Tag(db.Model):
    """
    Model for storing smart tags that can be applied to expenses
    Security: All queries filtered by user_id to ensure users only see their own tags
    """
    __tablename__ = 'tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(7), default='#6366f1')
    icon = db.Column(db.String(50), default='label')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_auto = db.Column(db.Boolean, default=False)  # True if auto-generated from OCR
    use_count = db.Column(db.Integer, default=0)  # Track how often used
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to expenses through junction table
    expenses = db.relationship('Expense', secondary='expense_tags', backref='tag_objects', lazy='dynamic')
    
    __table_args__ = (
        db.UniqueConstraint('name', 'user_id', name='unique_tag_per_user'),
    )
    
    def __repr__(self):
        return f'<Tag {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'icon': self.icon,
            'is_auto': self.is_auto,
            'use_count': self.use_count,
            'created_at': self.created_at.isoformat()
        }


class ExpenseTag(db.Model):
    """
    Junction table for many-to-many relationship between Expenses and Tags
    Security: Access controlled through Expense and Tag models
    """
    __tablename__ = 'expense_tags'
    
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('expenses.id', ondelete='CASCADE'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('expense_id', 'tag_id', name='unique_expense_tag'),
    )
    
    def __repr__(self):
        return f'<ExpenseTag expense_id={self.expense_id} tag_id={self.tag_id}>'


class SavingsGoal(db.Model):
    """
    Model for storing user savings goals (vacation, emergency fund, new car, etc.)
    Security: All queries filtered by user_id to ensure users only see their own goals
    """
    __tablename__ = 'savings_goals'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(3), nullable=False)
    icon = db.Column(db.String(50), default='savings')
    color = db.Column(db.String(7), default='#2b8cee')
    category = db.Column(db.String(50), default='custom')  # vacation, emergency, car, house, education, wedding, retirement, custom
    target_date = db.Column(db.DateTime, nullable=True)  # Optional deadline
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship for contributions
    contributions = db.relationship('SavingsContribution', backref='goal', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<SavingsGoal {self.name} - {self.current_amount}/{self.target_amount} {self.currency}>'
    
    def get_progress_percentage(self):
        """Calculate progress percentage"""
        if self.target_amount <= 0:
            return 0
        percentage = (self.current_amount / self.target_amount) * 100
        return min(round(percentage, 1), 100)
    
    def get_remaining_amount(self):
        """Calculate remaining amount to reach goal"""
        return max(self.target_amount - self.current_amount, 0)
    
    def get_days_remaining(self):
        """Calculate days until target date"""
        if not self.target_date:
            return None
        delta = self.target_date - datetime.utcnow()
        return max(delta.days, 0)
    
    def get_monthly_target(self):
        """Calculate how much to save monthly to reach goal by target date"""
        if not self.target_date:
            return None
        remaining = self.get_remaining_amount()
        days = self.get_days_remaining()
        if not days or days <= 0:
            return remaining
        months = days / 30
        if months <= 0:
            return remaining
        return round(remaining / months, 2)
    
    def check_milestone(self):
        """Check if user has reached a milestone (25%, 50%, 75%, 100%)"""
        percentage = self.get_progress_percentage()
        milestones = [25, 50, 75, 100]
        for milestone in milestones:
            if percentage >= milestone:
                return milestone
        return 0
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'target_amount': self.target_amount,
            'current_amount': self.current_amount,
            'currency': self.currency,
            'icon': self.icon,
            'color': self.color,
            'category': self.category,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'is_completed': self.is_completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'is_active': self.is_active,
            'progress_percentage': self.get_progress_percentage(),
            'remaining_amount': self.get_remaining_amount(),
            'days_remaining': self.get_days_remaining(),
            'monthly_target': self.get_monthly_target(),
            'milestone': self.check_milestone(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class SavingsContribution(db.Model):
    """
    Model for tracking individual contributions to savings goals
    Security: Access controlled through SavingsGoal model (user_id filter)
    """
    __tablename__ = 'savings_contributions'
    
    id = db.Column(db.Integer, primary_key=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('savings_goals.id', ondelete='CASCADE'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    note = db.Column(db.String(200), nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SavingsContribution {self.amount} to goal_id={self.goal_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'goal_id': self.goal_id,
            'amount': self.amount,
            'note': self.note,
            'date': self.date.isoformat(),
            'created_at': self.created_at.isoformat()
        }


class SpendingInsight(db.Model):
    """
    Model for storing smart spending insights (unusual spending alerts, weekly digests, etc.)
    Security: All queries filtered by user_id to ensure users only see their own insights
    """
    __tablename__ = 'spending_insights'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Insight type: unusual_spending, weekly_digest, money_leak, category_spike, budget_trend
    insight_type = db.Column(db.String(50), nullable=False)
    
    # Priority: low, medium, high, critical
    priority = db.Column(db.String(20), default='medium')
    
    # Title translation key (e.g., 'insights.unusualSpending.title')
    title_key = db.Column(db.String(100), nullable=False)
    
    # Message translation key
    message_key = db.Column(db.String(100), nullable=False)
    
    # Dynamic parameters for the message (JSON)
    message_params = db.Column(db.Text, default='{}')
    
    # Related category (if applicable)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    
    # Related amount (for display)
    amount = db.Column(db.Float, nullable=True)
    
    # Comparison data (e.g., last month's amount, percentage change)
    comparison_data = db.Column(db.Text, default='{}')  # JSON
    
    # Action key (suggestion for user)
    action_key = db.Column(db.String(100), nullable=True)
    
    # Icon for display
    icon = db.Column(db.String(50), default='insights')
    
    # Read/dismissed status
    is_read = db.Column(db.Boolean, default=False)
    is_dismissed = db.Column(db.Boolean, default=False)
    
    # For weekly digests, track the week
    period_start = db.Column(db.DateTime, nullable=True)
    period_end = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)  # Insights can expire
    
    # Relationships
    category = db.relationship('Category', backref='insights')
    user = db.relationship('User', backref='spending_insights')
    
    def __repr__(self):
        return f'<SpendingInsight {self.insight_type} for user {self.user_id}>'
    
    def get_message_params(self):
        try:
            return json.loads(self.message_params)
        except:
            return {}
    
    def set_message_params(self, params):
        self.message_params = json.dumps(params)
    
    def get_comparison_data(self):
        try:
            return json.loads(self.comparison_data)
        except:
            return {}
    
    def set_comparison_data(self, data):
        self.comparison_data = json.dumps(data)
    
    def to_dict(self):
        return {
            'id': self.id,
            'insight_type': self.insight_type,
            'priority': self.priority,
            'title_key': self.title_key,
            'message_key': self.message_key,
            'message_params': self.get_message_params(),
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'category_color': self.category.color if self.category else None,
            'amount': self.amount,
            'comparison_data': self.get_comparison_data(),
            'action_key': self.action_key,
            'icon': self.icon,
            'is_read': self.is_read,
            'is_dismissed': self.is_dismissed,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }


class UserInsightPreferences(db.Model):
    """
    Model for storing user preferences for spending insights notifications
    Security: One record per user
    """
    __tablename__ = 'user_insight_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Weekly digest preferences
    weekly_digest_enabled = db.Column(db.Boolean, default=True)
    weekly_digest_day = db.Column(db.Integer, default=0)  # 0=Monday, 6=Sunday
    
    # Unusual spending alerts
    unusual_spending_enabled = db.Column(db.Boolean, default=True)
    unusual_spending_threshold = db.Column(db.Float, default=1.5)  # 150% of average
    
    # Category comparison alerts
    category_alerts_enabled = db.Column(db.Boolean, default=True)
    category_alert_threshold = db.Column(db.Float, default=1.25)  # 125% of last month
    
    # Money leak detection
    money_leak_detection_enabled = db.Column(db.Boolean, default=True)
    money_leak_min_occurrences = db.Column(db.Integer, default=3)  # Minimum times to detect
    
    # Push notification preferences
    push_notifications_enabled = db.Column(db.Boolean, default=True)
    
    # Email preferences (for future use)
    email_digest_enabled = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('insight_preferences', uselist=False))
    
    def __repr__(self):
        return f'<UserInsightPreferences for user {self.user_id}>'
    
    def to_dict(self):
        return {
            'weekly_digest_enabled': self.weekly_digest_enabled,
            'weekly_digest_day': self.weekly_digest_day,
            'unusual_spending_enabled': self.unusual_spending_enabled,
            'unusual_spending_threshold': self.unusual_spending_threshold,
            'category_alerts_enabled': self.category_alerts_enabled,
            'category_alert_threshold': self.category_alert_threshold,
            'money_leak_detection_enabled': self.money_leak_detection_enabled,
            'money_leak_min_occurrences': self.money_leak_min_occurrences,
            'push_notifications_enabled': self.push_notifications_enabled,
            'email_digest_enabled': self.email_digest_enabled
        }

# ============================================================================
# GAMIFICATION MODELS
# ============================================================================

class Achievement(db.Model):
    """
    Model for storing user achievements and badges
    Security: All queries filtered by user_id
    """
    __tablename__ = 'achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Achievement type: no_spend_day, savings_streak, weekly_challenge, milestone, habit
    achievement_type = db.Column(db.String(50), nullable=False)
    
    # Unique achievement code (e.g., 'first_no_spend_day', 'streak_7_days', '52_week_complete')
    code = db.Column(db.String(100), nullable=False)
    
    # Display info (translation keys)
    title_key = db.Column(db.String(100), nullable=False)
    description_key = db.Column(db.String(100), nullable=False)
    
    # Badge visual
    icon = db.Column(db.String(50), default='emoji_events')
    badge_color = db.Column(db.String(7), default='#f59e0b')  # Gold by default
    
    # Rarity: common, uncommon, rare, epic, legendary
    rarity = db.Column(db.String(20), default='common')
    
    # Points earned for this achievement
    points = db.Column(db.Integer, default=10)
    
    # Progress tracking (for multi-step achievements)
    current_progress = db.Column(db.Integer, default=0)
    target_progress = db.Column(db.Integer, default=1)
    is_completed = db.Column(db.Boolean, default=False)
    
    # When completed
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Notification shown
    notification_shown = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', backref=db.backref('achievements', lazy='dynamic'))
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'code', name='unique_user_achievement'),
    )
    
    def __repr__(self):
        return f'<Achievement {self.code} for user {self.user_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'achievement_type': self.achievement_type,
            'code': self.code,
            'title_key': self.title_key,
            'description_key': self.description_key,
            'icon': self.icon,
            'badge_color': self.badge_color,
            'rarity': self.rarity,
            'points': self.points,
            'current_progress': self.current_progress,
            'target_progress': self.target_progress,
            'is_completed': self.is_completed,
            'progress_percentage': round((self.current_progress / self.target_progress * 100), 1) if self.target_progress > 0 else 0,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat()
        }


class Challenge(db.Model):
    """
    Model for storing active user challenges (no-spend days, 52-week, etc.)
    Security: All queries filtered by user_id
    """
    __tablename__ = 'challenges'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Challenge type: no_spend_day, no_spend_week, weekly_52, savings_streak, custom
    challenge_type = db.Column(db.String(50), nullable=False)
    
    # Display info
    title_key = db.Column(db.String(100), nullable=False)
    description_key = db.Column(db.String(100), nullable=False)
    
    # Challenge configuration (JSON)
    config = db.Column(db.Text, default='{}')  # e.g., target_amount, allowed_categories
    
    # Progress
    current_streak = db.Column(db.Integer, default=0)
    best_streak = db.Column(db.Integer, default=0)
    total_completed = db.Column(db.Integer, default=0)  # Total successful completions
    total_saved = db.Column(db.Float, default=0.0)  # For savings challenges
    
    # For 52-week challenge
    current_week = db.Column(db.Integer, default=1)
    weekly_amounts = db.Column(db.Text, default='{}')  # JSON: {week: amount}
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_completed = db.Column(db.Boolean, default=False)
    
    # Dates
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=True)  # Optional end date
    last_check_date = db.Column(db.DateTime, nullable=True)  # Last time challenge was checked
    completed_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('challenges', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Challenge {self.challenge_type} for user {self.user_id}>'
    
    def get_config(self):
        try:
            return json.loads(self.config)
        except:
            return {}
    
    def set_config(self, config_dict):
        self.config = json.dumps(config_dict)
    
    def get_weekly_amounts(self):
        try:
            return json.loads(self.weekly_amounts)
        except:
            return {}
    
    def set_weekly_amounts(self, amounts_dict):
        self.weekly_amounts = json.dumps(amounts_dict)
    
    def to_dict(self):
        return {
            'id': self.id,
            'challenge_type': self.challenge_type,
            'title_key': self.title_key,
            'description_key': self.description_key,
            'config': self.get_config(),
            'current_streak': self.current_streak,
            'best_streak': self.best_streak,
            'total_completed': self.total_completed,
            'total_saved': self.total_saved,
            'current_week': self.current_week,
            'weekly_amounts': self.get_weekly_amounts(),
            'is_active': self.is_active,
            'is_completed': self.is_completed,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'last_check_date': self.last_check_date.isoformat() if self.last_check_date else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat()
        }


class NoSpendDay(db.Model):
    """
    Model for tracking no-spend days
    Security: All queries filtered by user_id
    """
    __tablename__ = 'no_spend_days'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # The date of the no-spend day
    date = db.Column(db.Date, nullable=False)
    
    # Status: pending (end of day not reached), success, failed
    status = db.Column(db.String(20), default='pending')
    
    # Amount spent (0 for success)
    amount_spent = db.Column(db.Float, default=0.0)
    
    # If user set this as intentional no-spend day
    is_intentional = db.Column(db.Boolean, default=False)
    
    # Notes
    notes = db.Column(db.String(255), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('no_spend_days', lazy='dynamic'))
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'date', name='unique_user_date'),
    )
    
    def __repr__(self):
        return f'<NoSpendDay {self.date} for user {self.user_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'status': self.status,
            'amount_spent': self.amount_spent,
            'is_intentional': self.is_intentional,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }


class UserGamificationStats(db.Model):
    """
    Model for storing aggregated user gamification statistics
    Security: One record per user
    """
    __tablename__ = 'user_gamification_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Total points from all achievements
    total_points = db.Column(db.Integer, default=0)
    
    # Level (calculated from points)
    level = db.Column(db.Integer, default=1)
    
    # Streaks
    current_no_spend_streak = db.Column(db.Integer, default=0)
    best_no_spend_streak = db.Column(db.Integer, default=0)
    current_savings_streak = db.Column(db.Integer, default=0)  # Consecutive weeks saving
    best_savings_streak = db.Column(db.Integer, default=0)
    
    # Counters
    total_no_spend_days = db.Column(db.Integer, default=0)
    total_challenges_completed = db.Column(db.Integer, default=0)
    total_achievements_earned = db.Column(db.Integer, default=0)
    
    # 52-week challenge progress
    week_52_progress = db.Column(db.Integer, default=0)  # Weeks completed
    week_52_total_saved = db.Column(db.Float, default=0.0)
    
    # Badges earned (for quick access)
    badges_earned = db.Column(db.Text, default='[]')  # JSON array of badge codes
    
    # Last activity
    last_achievement_at = db.Column(db.DateTime, nullable=True)
    last_challenge_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('gamification_stats', uselist=False))
    
    def __repr__(self):
        return f'<UserGamificationStats for user {self.user_id}>'
    
    def get_badges_earned(self):
        try:
            return json.loads(self.badges_earned)
        except:
            return []
    
    def add_badge(self, badge_code):
        badges = self.get_badges_earned()
        if badge_code not in badges:
            badges.append(badge_code)
            self.badges_earned = json.dumps(badges)
    
    def calculate_level(self):
        """Calculate level based on total points"""
        # Level thresholds: 0-99=1, 100-249=2, 250-499=3, 500-999=4, 1000-1999=5, etc.
        thresholds = [0, 100, 250, 500, 1000, 2000, 4000, 8000, 15000, 30000]
        for i, threshold in enumerate(thresholds):
            if self.total_points < threshold:
                self.level = i
                return
        self.level = len(thresholds)
    
    def to_dict(self):
        return {
            'total_points': self.total_points,
            'level': self.level,
            'current_no_spend_streak': self.current_no_spend_streak,
            'best_no_spend_streak': self.best_no_spend_streak,
            'current_savings_streak': self.current_savings_streak,
            'best_savings_streak': self.best_savings_streak,
            'total_no_spend_days': self.total_no_spend_days,
            'total_challenges_completed': self.total_challenges_completed,
            'total_achievements_earned': self.total_achievements_earned,
            'week_52_progress': self.week_52_progress,
            'week_52_total_saved': self.week_52_total_saved,
            'badges_earned': self.get_badges_earned(),
            'last_achievement_at': self.last_achievement_at.isoformat() if self.last_achievement_at else None,
            'last_challenge_at': self.last_challenge_at.isoformat() if self.last_challenge_at else None
        }


class SecurityLog(db.Model):
    """Security audit log for tracking important security events"""
    __tablename__ = 'security_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Nullable for failed logins
    event_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 can be up to 45 chars
    user_agent = db.Column(db.String(500), nullable=True)
    success = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Event types:
    # LOGIN_SUCCESS, LOGIN_FAILED, LOGOUT
    # PASSWORD_CHANGE, PASSWORD_RESET_REQUEST, PASSWORD_RESET_COMPLETE
    # 2FA_ENABLED, 2FA_DISABLED, 2FA_USED
    # ACCOUNT_LOCKED, ACCOUNT_UNLOCKED
    # ADMIN_ACTION, SETTINGS_CHANGE
    
    user = db.relationship('User', backref=db.backref('security_logs', lazy='dynamic'))
    
    @classmethod
    def log(cls, event_type, user_id=None, description=None, ip_address=None, user_agent=None, success=True):
        """Create a security log entry"""
        from app import db
        log_entry = cls(
            user_id=user_id,
            event_type=event_type,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success
        )
        db.session.add(log_entry)
        db.session.commit()
        return log_entry
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'event_type': self.event_type,
            'description': self.description,
            'ip_address': self.ip_address,
            'success': self.success,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class UserNotification(db.Model):
    """In-app notifications for users (security alerts, etc.)"""
    __tablename__ = 'user_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # security, info, warning
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)
    
    # Notification types:
    # NEW_LOGIN - New login detected from different IP/device
    # FAILED_LOGINS - Multiple failed login attempts
    # PASSWORD_CHANGED - Password was changed
    # 2FA_CHANGED - 2FA settings modified
    # ACCOUNT_LOCKED - Account was locked
    
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))
    
    @classmethod
    def create(cls, user_id, notification_type, title, message=None):
        """Create a notification for a user"""
        from app import db
        notif = cls(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message
        )
        db.session.add(notif)
        db.session.commit()
        return notif
    
    def mark_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'notification_type': self.notification_type,
            'title': self.title,
            'message': self.message,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None
        }


class UserSession(db.Model):
    """Track active user sessions for security management"""
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_token = db.Column(db.String(64), unique=True, nullable=False)  # Unique session identifier
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    device_type = db.Column(db.String(50), nullable=True)  # mobile, desktop, tablet
    browser = db.Column(db.String(100), nullable=True)
    os = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(200), nullable=True)  # City, Country (from IP)
    is_current = db.Column(db.Boolean, default=False)  # Mark current session
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Login time
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    revoked_at = db.Column(db.DateTime, nullable=True)
    
    user = db.relationship('User', backref=db.backref('sessions', lazy='dynamic'))
    
    @classmethod
    def create_session(cls, user_id, request, session_token):
        """Create a new session record"""
        import secrets
        
        # Parse user agent for device info
        user_agent = request.headers.get('User-Agent', '')[:500]
        device_info = cls.parse_user_agent(user_agent)
        
        # Get IP address
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip_address and ',' in ip_address:
            ip_address = ip_address.split(',')[0].strip()
        
        session = cls(
            user_id=user_id,
            session_token=session_token,
            ip_address=ip_address,
            user_agent=user_agent,
            device_type=device_info.get('device_type', 'unknown'),
            browser=device_info.get('browser', 'Unknown'),
            os=device_info.get('os', 'Unknown'),
            is_active=True
        )
        db.session.add(session)
        db.session.commit()
        return session
    
    @staticmethod
    def parse_user_agent(user_agent):
        """Parse user agent string to extract device info"""
        user_agent_lower = user_agent.lower()
        
        # Detect device type
        device_type = 'desktop'
        if 'mobile' in user_agent_lower or 'android' in user_agent_lower:
            if 'tablet' in user_agent_lower or 'ipad' in user_agent_lower:
                device_type = 'tablet'
            else:
                device_type = 'mobile'
        elif 'tablet' in user_agent_lower or 'ipad' in user_agent_lower:
            device_type = 'tablet'
        
        # Detect browser
        browser = 'Unknown'
        if 'edg/' in user_agent_lower or 'edge' in user_agent_lower:
            browser = 'Edge'
        elif 'chrome' in user_agent_lower and 'chromium' not in user_agent_lower:
            browser = 'Chrome'
        elif 'firefox' in user_agent_lower:
            browser = 'Firefox'
        elif 'safari' in user_agent_lower and 'chrome' not in user_agent_lower:
            browser = 'Safari'
        elif 'opera' in user_agent_lower or 'opr/' in user_agent_lower:
            browser = 'Opera'
        
        # Detect OS
        os = 'Unknown'
        if 'windows' in user_agent_lower:
            os = 'Windows'
        elif 'mac os' in user_agent_lower or 'macos' in user_agent_lower:
            os = 'macOS'
        elif 'linux' in user_agent_lower and 'android' not in user_agent_lower:
            os = 'Linux'
        elif 'android' in user_agent_lower:
            os = 'Android'
        elif 'iphone' in user_agent_lower or 'ipad' in user_agent_lower:
            os = 'iOS'
        
        return {
            'device_type': device_type,
            'browser': browser,
            'os': os
        }
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()
        db.session.commit()
    
    def revoke(self):
        """Revoke/terminate this session"""
        self.is_active = False
        self.revoked_at = datetime.utcnow()
        db.session.commit()
    
    @classmethod
    def revoke_all_except(cls, user_id, current_session_token):
        """Revoke all sessions except the current one"""
        sessions = cls.query.filter(
            cls.user_id == user_id,
            cls.session_token != current_session_token,
            cls.is_active == True
        ).all()
        
        count = 0
        for session in sessions:
            session.is_active = False
            session.revoked_at = datetime.utcnow()
            count += 1
        
        db.session.commit()
        return count
    
    @classmethod
    def cleanup_expired(cls, days=30):
        """Clean up sessions older than specified days"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        cls.query.filter(cls.last_activity < cutoff).delete()
        db.session.commit()
    
    def to_dict(self, is_current=False):
        return {
            'id': self.id,
            'ip_address': self.ip_address,
            'device_type': self.device_type,
            'browser': self.browser,
            'os': self.os,
            'location': self.location,
            'is_current': is_current or self.is_current,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'is_active': self.is_active
        }