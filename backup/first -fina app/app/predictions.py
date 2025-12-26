"""
Spending Predictions Module
Analyzes historical spending patterns and predicts future expenses
"""

from app import db
from app.models.category import Category, Expense
from sqlalchemy import extract, func
from datetime import datetime, timedelta
from collections import defaultdict
import statistics


def get_spending_predictions(user_id, months_ahead=3):
    """
    Predict spending for the next X months based on historical data
    
    Args:
        user_id: User ID to generate predictions for
        months_ahead: Number of months to predict (default: 3)
    
    Returns:
        dict with predictions per category and total
    """
    categories = Category.query.filter_by(user_id=user_id).all()
    
    predictions = {
        'by_category': {},
        'total_months': 0,
        'insights': []
    }
    
    current_date = datetime.now()
    total_predicted = 0
    total_months_data = []
    
    for category in categories:
        category_prediction = predict_category_spending(
            category, 
            current_date, 
            months_ahead
        )
        
        if category_prediction['predicted_amount'] > 0:
            # Add category_id for API calls
            category_prediction['category_id'] = category.id
            predictions['by_category'][category.name] = category_prediction
            total_predicted += category_prediction['predicted_amount']
            total_months_data.append(category_prediction['historical_months'])
    
    # Calculate overall statistics
    if predictions['by_category']:
        avg_months = sum(total_months_data) / len(total_months_data)
        predictions['total_months'] = int(avg_months)
        
        # Determine overall confidence
        if avg_months >= 6:
            overall_confidence = 'high'
        elif avg_months >= 3:
            overall_confidence = 'medium'
        else:
            overall_confidence = 'low'
        
        # Determine overall trend
        increasing = sum(1 for p in predictions['by_category'].values() if p['trend'] == 'increasing')
        decreasing = sum(1 for p in predictions['by_category'].values() if p['trend'] == 'decreasing')
        
        if increasing > decreasing:
            overall_trend = 'increasing'
        elif decreasing > increasing:
            overall_trend = 'decreasing'
        else:
            overall_trend = 'stable'
        
        predictions['total'] = {
            'amount': round(total_predicted, 2),
            'confidence': overall_confidence,
            'trend': overall_trend,
            'months_of_data': int(avg_months)
        }
    else:
        predictions['total_months'] = 0
        predictions['total'] = {
            'amount': 0,
            'confidence': 'none',
            'trend': 'stable',
            'months_of_data': 0
        }
    
    # Generate insights
    predictions['insights'] = generate_insights(predictions['by_category'], current_date)
    
    return predictions


def predict_category_spending(category, current_date, months_ahead=3):
    """
    Predict spending for a specific category
    
    Uses weighted average with more recent months having higher weight
    """
    # Get last 12 months of data
    twelve_months_ago = current_date - timedelta(days=365)
    
    monthly_spending = db.session.query(
        extract('year', Expense.date).label('year'),
        extract('month', Expense.date).label('month'),
        func.sum(Expense.amount).label('total')
    ).filter(
        Expense.category_id == category.id,
        Expense.date >= twelve_months_ago
    ).group_by('year', 'month').all()
    
    if not monthly_spending:
        return {
            'predicted_amount': 0,
            'historical_average': 0,
            'trend': 'none',
            'historical_months': 0,
            'confidence': 'none'
        }
    
    # Extract amounts and calculate statistics
    amounts = [float(row.total) for row in monthly_spending]
    historical_months = len(amounts)
    
    # Calculate weighted average (recent months have more weight)
    weights = list(range(1, len(amounts) + 1))
    weighted_avg = sum(a * w for a, w in zip(amounts, weights)) / sum(weights)
    
    # Calculate trend
    if len(amounts) >= 3:
        first_half = sum(amounts[:len(amounts)//2]) / (len(amounts)//2)
        second_half = sum(amounts[len(amounts)//2:]) / (len(amounts) - len(amounts)//2)
        
        if second_half > first_half * 1.1:
            trend = 'increasing'
        elif second_half < first_half * 0.9:
            trend = 'decreasing'
        else:
            trend = 'stable'
    else:
        trend = 'stable'
    
    # Adjust prediction based on trend
    if trend == 'increasing':
        predicted_amount = weighted_avg * 1.05  # 5% increase
    elif trend == 'decreasing':
        predicted_amount = weighted_avg * 0.95  # 5% decrease
    else:
        predicted_amount = weighted_avg
    
    # Multiply by months ahead
    predicted_total = predicted_amount * months_ahead
    
    # Calculate confidence based on data consistency
    if len(amounts) >= 3:
        std_dev = statistics.stdev(amounts)
        avg = statistics.mean(amounts)
        coefficient_of_variation = std_dev / avg if avg > 0 else 1
        
        if coefficient_of_variation < 0.3:
            confidence = 'high'
        elif coefficient_of_variation < 0.6:
            confidence = 'medium'
        else:
            confidence = 'low'
    else:
        confidence = 'low'
    
    return {
        'predicted_amount': round(predicted_total, 2),
        'monthly_average': round(predicted_amount, 2),
        'historical_average': round(statistics.mean(amounts), 2),
        'trend': trend,
        'historical_months': historical_months,
        'confidence': confidence,
        'min': round(min(amounts), 2),
        'max': round(max(amounts), 2)
    }


def generate_insights(category_predictions, current_date):
    """Generate human-readable insights from predictions"""
    insights = []
    
    # Find categories with increasing trends
    increasing = [
        name for name, pred in category_predictions.items() 
        if pred['trend'] == 'increasing'
    ]
    if increasing:
        insights.append({
            'type': 'warning',
            'message': f"Spending is increasing in: {', '.join(increasing)}"
        })
    
    # Find categories with high spending
    sorted_by_amount = sorted(
        category_predictions.items(), 
        key=lambda x: x[1]['predicted_amount'], 
        reverse=True
    )
    
    if sorted_by_amount:
        top_category = sorted_by_amount[0]
        insights.append({
            'type': 'info',
            'message': f"Highest predicted spending: {top_category[0]}"
        })
    
    # Find categories with high confidence
    high_confidence = [
        name for name, pred in category_predictions.items() 
        if pred['confidence'] == 'high'
    ]
    if len(high_confidence) >= 3:
        insights.append({
            'type': 'success',
            'message': f"High prediction accuracy for {len(high_confidence)} categories"
        })
    
    # Seasonal insight (simple check)
    current_month = current_date.month
    if current_month in [11, 12]:  # November, December
        insights.append({
            'type': 'info',
            'message': "Holiday season - spending typically increases"
        })
    elif current_month in [1, 2]:  # January, February
        insights.append({
            'type': 'info',
            'message': "Post-holiday period - spending may decrease"
        })
    
    return insights


def get_category_forecast(category_id, user_id, months=6):
    """
    Get detailed forecast for a specific category
    
    Returns monthly predictions for next N months
    """
    category = Category.query.filter_by(
        id=category_id, 
        user_id=user_id
    ).first()
    
    if not category:
        return None
    
    current_date = datetime.now()
    
    # Get historical monthly data
    twelve_months_ago = current_date - timedelta(days=365)
    
    monthly_data = db.session.query(
        extract('year', Expense.date).label('year'),
        extract('month', Expense.date).label('month'),
        func.sum(Expense.amount).label('total')
    ).filter(
        Expense.category_id == category_id,
        Expense.date >= twelve_months_ago
    ).group_by('year', 'month').order_by('year', 'month').all()
    
    if not monthly_data:
        return {
            'category_name': category.name,
            'forecast': [],
            'message': 'Not enough data for predictions'
        }
    
    # Calculate base prediction
    amounts = [float(row.total) for row in monthly_data]
    avg_spending = statistics.mean(amounts)
    
    # Generate forecast for next months
    forecast = []
    for i in range(1, months + 1):
        future_date = current_date + timedelta(days=30 * i)
        
        # Simple seasonal adjustment based on month
        seasonal_factor = get_seasonal_factor(future_date.month)
        predicted = avg_spending * seasonal_factor
        
        forecast.append({
            'month': future_date.strftime('%B %Y'),
            'month_num': future_date.month,
            'year': future_date.year,
            'predicted_amount': round(predicted, 2)
        })
    
    return {
        'category_name': category.name,
        'category_color': category.color,
        'historical_average': round(avg_spending, 2),
        'forecast': forecast
    }


def get_seasonal_factor(month):
    """
    Get seasonal adjustment factor based on month
    
    This is a simplified version - could be made more sophisticated
    with actual historical data analysis
    """
    # Holiday months (Nov, Dec) typically have higher spending
    # Summer months might vary by category
    factors = {
        1: 0.9,   # January - post-holiday slowdown
        2: 0.95,  # February
        3: 1.0,   # March
        4: 1.0,   # April
        5: 1.05,  # May
        6: 1.05,  # June - summer
        7: 1.05,  # July - summer
        8: 1.0,   # August
        9: 1.0,   # September - back to school
        10: 1.05, # October
        11: 1.1,  # November - holidays starting
        12: 1.15  # December - peak holiday
    }
    return factors.get(month, 1.0)


def compare_with_predictions(user_id, month=None, year=None):
    """
    Compare actual spending with predictions
    
    Useful for showing accuracy of predictions
    """
    if month is None:
        month = datetime.now().month
    if year is None:
        year = datetime.now().year
    
    categories = Category.query.filter_by(user_id=user_id).all()
    
    comparison = {
        'month': month,
        'year': year,
        'categories': {}
    }
    
    for category in categories:
        # Get actual spending for the month
        actual = db.session.query(func.sum(Expense.amount)).filter(
            Expense.category_id == category.id,
            extract('year', Expense.date) == year,
            extract('month', Expense.date) == month
        ).scalar()
        
        actual = float(actual) if actual else 0
        
        # Get predicted value (simplified - using average)
        prediction = predict_category_spending(category, datetime.now(), 1)
        predicted = prediction['monthly_average']
        
        if predicted > 0:
            accuracy = (1 - abs(actual - predicted) / predicted) * 100
        else:
            accuracy = 0 if actual == 0 else 0
        
        comparison['categories'][category.name] = {
            'actual': round(actual, 2),
            'predicted': round(predicted, 2),
            'difference': round(actual - predicted, 2),
            'accuracy': round(accuracy, 1)
        }
    
    return comparison
