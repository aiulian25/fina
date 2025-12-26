# Budget Alerts Feature

## Overview
The Budget Alerts feature allows users to set spending limits on categories and receive email notifications when they exceed their budget.

## Features

### 1. Category Budgets
- Set monthly budget limits per category
- Configure alert threshold (50-200% of budget)
- Visual budget status in category edit form
- Automatic monthly reset

### 2. Email Notifications
- Beautiful HTML emails with progress bars
- Multilingual support (English, Romanian, Spanish)
- Shows spent amount, budget, and percentage over
- Smart alerts (only one email per month per category)

### 3. User Preferences
- Global enable/disable toggle for budget alerts
- Optional separate email for alerts
- Settings available in user profile

## Configuration

### Environment Variables
Add these to your `.env` file or environment:

```bash
# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@fina.app

# Application URL (for links in emails)
APP_URL=http://localhost:5001
```

### Gmail Setup
If using Gmail:
1. Enable 2-factor authentication on your Google account
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Use the app password as `MAIL_PASSWORD`

### Other SMTP Providers
- **SendGrid**: `smtp.sendgrid.net`, Port 587
- **Mailgun**: `smtp.mailgun.org`, Port 587
- **Amazon SES**: `email-smtp.region.amazonaws.com`, Port 587
- **Outlook**: `smtp-mail.outlook.com`, Port 587

## Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Migration
```bash
python migrations/migrate_budget_alerts.py
```

Or manually with SQL:
```bash
sqlite3 instance/finance_tracker.db < migrations/add_budget_alerts.sql
```

### 3. Restart Application
```bash
docker-compose restart
# or
python wsgi.py
```

## Usage

### Setting Up Category Budgets

1. Navigate to a category (Dashboard → Category)
2. Click "Edit Category"
3. Scroll to "Budget Management" section
4. Set:
   - **Monthly Budget Limit**: Your spending limit (e.g., $500)
   - **Alert Threshold**: When to notify (e.g., 100% = notify at $500, 80% = notify at $400)
5. Save changes

### Enabling Alerts

1. Go to Settings (top-right menu)
2. Scroll to "Budget Alert Settings"
3. Check "Enable budget alert emails"
4. (Optional) Enter separate email for alerts
5. Save profile

### How Alerts Work

1. **Expense Added**: Every time you add an expense, the system checks all budgets
2. **Threshold Check**: If spending reaches the threshold percentage, an alert is sent
3. **One Per Month**: You'll only receive one alert per category per month
4. **Monthly Reset**: At the start of each month, alerts reset automatically
5. **User Control**: Alerts only sent if user has enabled them globally

### Example Scenarios

#### Scenario 1: Standard Budget
- Budget: $500
- Threshold: 100%
- Spending: $520
- **Result**: Email sent when spending hits $500+

#### Scenario 2: Early Warning
- Budget: $1000
- Threshold: 80%
- Spending: $850
- **Result**: Email sent at $800 (80% of $1000)

#### Scenario 3: Overspending Alert
- Budget: $300
- Threshold: 150%
- Spending: $480
- **Result**: Email sent at $450 (150% of $300)

## Email Template

Emails include:
- Category name and icon
- Current spending vs. budget
- Percentage over budget
- Visual progress bar
- Link to view category details
- Localized in user's preferred language

## Technical Details

### Database Schema

**Category Table** (new columns):
```sql
monthly_budget REAL                -- Optional budget limit
budget_alert_sent BOOLEAN           -- Flag to prevent duplicate alerts
budget_alert_threshold INTEGER      -- Percentage (50-200) to trigger alert
last_budget_check DATE              -- For monthly reset logic
```

**User Table** (new columns):
```sql
budget_alerts_enabled BOOLEAN       -- Global toggle for alerts
alert_email VARCHAR(120)            -- Optional separate email
```

### Key Functions

**`check_budget_alerts()`**
- Scans all categories with budgets
- Calculates current month spending
- Sends alerts for over-budget categories
- Respects user preferences

**`send_budget_alert(category, user, budget_info)`**
- Generates HTML email with progress bars
- Localizes content based on user language
- Sends via Flask-Mail
- Updates `budget_alert_sent` flag

**`Category.get_budget_status()`**
- Returns: `{spent, budget, percentage, over_budget}`
- Calculates current month spending
- Used by UI and email system

**`Category.should_send_budget_alert()`**
- Checks if alert should be sent
- Logic: has budget + over threshold + not sent this month
- Handles monthly reset automatically

### Security Considerations

- ✅ User isolation: Only checks categories owned by user
- ✅ Email validation: Validates alert_email format
- ✅ CSRF protection: All forms protected
- ✅ SQL injection: Uses SQLAlchemy ORM
- ✅ XSS prevention: Email content properly escaped
- ✅ Rate limiting: One alert per category per month

### Performance

- Indexes on budget-related columns
- Check only runs after expense creation
- No scheduled jobs required (event-driven)
- Efficient queries using SQLAlchemy relationships

## Troubleshooting

### Emails Not Sending

**Check SMTP Configuration:**
```python
# In Python console
from app import create_app
app = create_app()
print(app.config['MAIL_SERVER'])
print(app.config['MAIL_PORT'])
print(app.config['MAIL_USERNAME'])
```

**Test Email Sending:**
```python
from app.budget_alerts import send_test_budget_alert
send_test_budget_alert('your-email@example.com')
```

**Common Issues:**
- Gmail: Must use App Password, not regular password
- Firewall: Port 587 must be open
- TLS: Set `MAIL_USE_TLS=true` for most providers
- Credentials: Check username/password are correct

### Alerts Not Triggering

1. **Check User Settings**: Ensure "Enable budget alert emails" is checked
2. **Check Category Budget**: Verify monthly_budget is set
3. **Check Threshold**: Spending must exceed threshold percentage
4. **Check Monthly Reset**: Alert may have been sent already this month
5. **Check Logs**: Look for errors in application logs

### Migration Errors

**Column already exists:**
```
Migration already applied, no action needed
```

**Database locked:**
```bash
# Stop application first
docker-compose down
python migrations/migrate_budget_alerts.py
docker-compose up -d
```

## API Reference

### Budget Alert Functions

```python
from app.budget_alerts import check_budget_alerts, send_test_budget_alert

# Check all budgets for current user
check_budget_alerts()

# Send test email
send_test_budget_alert('test@example.com')
```

### Category Methods

```python
from app.models.category import Category

category = Category.query.get(1)

# Get current month spending
spending = category.get_current_month_spending()

# Get budget status
status = category.get_budget_status()
# Returns: {'spent': 520.0, 'budget': 500.0, 'percentage': 104.0, 'over_budget': True}

# Check if alert should be sent
should_send = category.should_send_budget_alert()
```

## Future Enhancements

Potential improvements:
- [ ] Budget overview dashboard widget
- [ ] Budget vs. actual spending charts
- [ ] Weekly budget summaries
- [ ] Budget recommendations based on spending patterns
- [ ] Push notifications for PWA
- [ ] SMS alerts integration
- [ ] Multi-currency budget support
- [ ] Budget rollover (unused budget carries to next month)
- [ ] Budget sharing for family accounts

## Support

For issues or questions:
1. Check application logs: `docker logs finance-tracker-web-1`
2. Review SMTP configuration
3. Test email sending with `send_test_budget_alert()`
4. Verify database migration completed

## License

Same as FINA application license.
