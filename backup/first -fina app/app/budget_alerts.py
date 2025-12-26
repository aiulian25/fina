"""
Budget Alert System
Monitors spending and sends email alerts when budget limits are exceeded
"""

from flask import render_template_string
from flask_mail import Mail, Message
from app.models.category import Category
from app.models.user import User
from app import db
from datetime import datetime
import os

mail = None

def init_mail(app):
    """Initialize Flask-Mail with app configuration"""
    global mail
    
    # Email configuration from environment variables
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@fina.app')
    
    mail = Mail(app)
    return mail


def check_budget_alerts():
    """Check all categories for budget overruns and send alerts"""
    if not mail:
        print("[Budget Alerts] Mail not configured")
        return 0
    
    alerts_sent = 0
    
    # Get all categories with budgets that need checking
    categories = Category.query.filter(
        Category.monthly_budget.isnot(None),
        Category.monthly_budget > 0
    ).all()
    
    for category in categories:
        if category.should_send_budget_alert():
            user = User.query.get(category.user_id)
            
            if user and user.budget_alerts_enabled:
                if send_budget_alert(user, category):
                    category.budget_alert_sent = True
                    category.last_budget_check = datetime.now()
                    alerts_sent += 1
    
    db.session.commit()
    return alerts_sent


def send_budget_alert(user, category):
    """Send budget alert email to user"""
    if not mail:
        print(f"[Budget Alert] Mail not configured, skipping alert for {user.email}")
        return False
    
    try:
        status = category.get_budget_status()
        alert_email = user.alert_email or user.email
        
        # Get user's language
        lang = user.language or 'en'
        
        # Email templates in multiple languages
        subjects = {
            'en': f'⚠️ Budget Alert: {category.name}',
            'ro': f'⚠️ Alertă Buget: {category.name}',
            'es': f'⚠️ Alerta de Presupuesto: {category.name}'
        }
        
        # Email body template
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #4c1d95 0%, #3b0764 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; }}
                .alert-box {{ background: #fef2f2; border-left: 4px solid #ef4444; 
                             padding: 20px; margin: 20px 0; border-radius: 5px; }}
                .budget-details {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .stat {{ display: inline-block; margin: 10px 20px 10px 0; }}
                .stat-label {{ color: #6b7280; font-size: 14px; }}
                .stat-value {{ font-size: 24px; font-weight: bold; color: #1f2937; }}
                .over-budget {{ color: #ef4444; }}
                .progress-bar {{ background: #e5e7eb; height: 30px; border-radius: 15px; 
                                overflow: hidden; margin: 20px 0; }}
                .progress-fill {{ background: {progress_color}; height: 100%; 
                                 transition: width 0.3s; display: flex; align-items: center; 
                                 justify-content: center; color: white; font-weight: bold; }}
                .button {{ display: inline-block; background: #5b5fc7; color: white; 
                          padding: 12px 30px; text-decoration: none; border-radius: 8px; 
                          margin: 20px 0; }}
                .footer {{ text-align: center; color: #6b7280; font-size: 14px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔔 {title}</h1>
                </div>
                <div class="content">
                    <div class="alert-box">
                        <h2 style="margin-top: 0;">⚠️ {alert_message}</h2>
                        <p>{alert_description}</p>
                    </div>
                    
                    <div class="budget-details">
                        <h3>{details_title}</h3>
                        
                        <div class="stat">
                            <div class="stat-label">{spent_label}</div>
                            <div class="stat-value over-budget">{currency}{spent:.2f}</div>
                        </div>
                        
                        <div class="stat">
                            <div class="stat-label">{budget_label}</div>
                            <div class="stat-value">{currency}{budget:.2f}</div>
                        </div>
                        
                        <div class="stat">
                            <div class="stat-label">{remaining_label}</div>
                            <div class="stat-value" style="color: #ef4444;">{currency}{remaining:.2f}</div>
                        </div>
                        
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {percentage}%;">
                                {percentage:.1f}%
                            </div>
                        </div>
                        
                        <p style="margin-top: 20px; color: #6b7280;">
                            <strong>{category_label}:</strong> {category_name}<br>
                            <strong>{threshold_label}:</strong> {threshold}%
                        </p>
                    </div>
                    
                    <center>
                        <a href="{dashboard_url}" class="button">{button_text}</a>
                    </center>
                    
                    <div class="footer">
                        <p>{footer_text}</p>
                        <p style="font-size: 12px;">{disable_text}</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Translations
        translations = {
            'en': {
                'title': 'Budget Alert',
                'alert_message': 'Budget Limit Exceeded!',
                'alert_description': f'Your spending in the "{category.name}" category has exceeded {int(category.budget_alert_threshold * 100)}% of your monthly budget.',
                'details_title': 'Budget Overview',
                'spent_label': 'Spent This Month',
                'budget_label': 'Monthly Budget',
                'remaining_label': 'Over Budget',
                'category_label': 'Category',
                'threshold_label': 'Alert Threshold',
                'button_text': 'View Dashboard',
                'footer_text': 'This is an automated budget alert from FINA Finance Tracker.',
                'disable_text': 'To disable budget alerts, go to Settings > Profile.'
            },
            'ro': {
                'title': 'Alertă Buget',
                'alert_message': 'Limită buget depășită!',
                'alert_description': f'Cheltuielile în categoria "{category.name}" au depășit {int(category.budget_alert_threshold * 100)}% din bugetul lunar.',
                'details_title': 'Rezumat Buget',
                'spent_label': 'Cheltuit Luna Aceasta',
                'budget_label': 'Buget Lunar',
                'remaining_label': 'Peste Buget',
                'category_label': 'Categorie',
                'threshold_label': 'Prag Alertă',
                'button_text': 'Vezi Tabloul de Bord',
                'footer_text': 'Aceasta este o alertă automată de buget de la FINA Finance Tracker.',
                'disable_text': 'Pentru a dezactiva alertele de buget, mergi la Setări > Profil.'
            },
            'es': {
                'title': 'Alerta de Presupuesto',
                'alert_message': '¡Límite de presupuesto excedido!',
                'alert_description': f'Tus gastos en la categoría "{category.name}" han superado el {int(category.budget_alert_threshold * 100)}% de tu presupuesto mensual.',
                'details_title': 'Resumen de Presupuesto',
                'spent_label': 'Gastado Este Mes',
                'budget_label': 'Presupuesto Mensual',
                'remaining_label': 'Sobre Presupuesto',
                'category_label': 'Categoría',
                'threshold_label': 'Umbral de Alerta',
                'button_text': 'Ver Panel',
                'footer_text': 'Esta es una alerta automática de presupuesto de FINA Finance Tracker.',
                'disable_text': 'Para desactivar las alertas de presupuesto, ve a Configuración > Perfil.'
            }
        }
        
        t = translations.get(lang, translations['en'])
        
        # Determine progress bar color
        if status['percentage'] >= 100:
            progress_color = '#ef4444'  # Red
        elif status['percentage'] >= 90:
            progress_color = '#f59e0b'  # Orange
        else:
            progress_color = '#10b981'  # Green
        
        # Dashboard URL (adjust based on your deployment)
        dashboard_url = os.environ.get('APP_URL', 'http://localhost:5001') + '/dashboard'
        
        html_body = html_template.format(
            title=t['title'],
            alert_message=t['alert_message'],
            alert_description=t['alert_description'],
            details_title=t['details_title'],
            spent_label=t['spent_label'],
            budget_label=t['budget_label'],
            remaining_label=t['remaining_label'],
            category_label=t['category_label'],
            threshold_label=t['threshold_label'],
            button_text=t['button_text'],
            footer_text=t['footer_text'],
            disable_text=t['disable_text'],
            currency=user.currency,
            spent=status['spent'],
            budget=status['budget'],
            remaining=abs(status['remaining']),
            percentage=min(status['percentage'], 100),
            progress_color=progress_color,
            category_name=category.name,
            threshold=int(category.budget_alert_threshold * 100),
            dashboard_url=dashboard_url
        )
        
        msg = Message(
            subject=subjects.get(lang, subjects['en']),
            recipients=[alert_email],
            html=html_body
        )
        
        mail.send(msg)
        print(f"[Budget Alert] Sent to {alert_email} for category {category.name}")
        return True
        
    except Exception as e:
        print(f"[Budget Alert] Error sending email: {e}")
        return False


def send_test_budget_alert(user_email):
    """Send a test budget alert email"""
    if not mail:
        return False, "Mail not configured"
    
    try:
        msg = Message(
            subject='Test Budget Alert - FINA',
            recipients=[user_email],
            body='This is a test email from FINA budget alert system. If you received this, email alerts are working correctly!',
            html='''
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2>✅ Test Email Successful</h2>
                    <p>This is a test email from the FINA budget alert system.</p>
                    <p>If you received this message, your email configuration is working correctly!</p>
                    <hr>
                    <p style="color: #666; font-size: 12px;">FINA Finance Tracker</p>
                </body>
            </html>
            '''
        )
        mail.send(msg)
        return True, "Test email sent successfully"
    except Exception as e:
        return False, str(e)
