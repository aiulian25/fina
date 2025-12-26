from app import db
from flask_login import UserMixin
from datetime import datetime
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
    avatar = db.Column(db.String(255), default='icons/avatars/avatar-1.svg')
    monthly_budget = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    expenses = db.relationship('Expense', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    income = db.relationship('Income', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    categories = db.relationship('Category', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    documents = db.relationship('Document', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    recurring_expenses = db.relationship('RecurringExpense', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
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
        return self.tag_objects.all()
    
    def add_tag(self, tag):
        """Add a tag to this expense"""
        if tag not in self.tag_objects.all():
            self.tag_objects.append(tag)
            tag.use_count += 1
    
    def remove_tag(self, tag):
        """Remove a tag from this expense"""
        if tag in self.tag_objects.all():
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
    
    category = db.relationship('Category', backref='recurring_expenses')
    
    def __repr__(self):
        return f'<RecurringExpense {self.name} - {self.amount} {self.currency}>'
    
    def to_dict(self):
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

