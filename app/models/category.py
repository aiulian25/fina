from app import db
from datetime import datetime
from sqlalchemy import func, extract

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#6366f1')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    expenses = db.relationship('Expense', backref='category', lazy=True, cascade='all, delete-orphan')
    
    def get_total_spent(self):
        return sum(expense.amount for expense in self.expenses)
    
    def get_monthly_totals(self, year=None):
        """Get expenses grouped by month for the year"""
        if year is None:
            year = datetime.now().year
        
        monthly_data = db.session.query(
            extract('month', Expense.date).label('month'),
            func.sum(Expense.amount).label('total')
        ).filter(
            Expense.category_id == self.id,
            extract('year', Expense.date) == year
        ).group_by('month').all()
        
        # Create array with all 12 months
        result = [0] * 12
        for month, total in monthly_data:
            result[int(month) - 1] = float(total) if total else 0
        
        return result
    
    def get_yearly_total(self, year):
        """Get total expenses for a specific year"""
        total = db.session.query(func.sum(Expense.amount)).filter(
            Expense.category_id == self.id,
            extract('year', Expense.date) == year
        ).scalar()
        return float(total) if total else 0
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Expense(db.Model):
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    paid_by = db.Column(db.String(100))
    tags = db.Column(db.String(500))
    file_path = db.Column(db.String(500))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Expense {self.description}: ${self.amount}>'
