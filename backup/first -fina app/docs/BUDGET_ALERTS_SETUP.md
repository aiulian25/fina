# Budget Alerts Setup Guide

## Quick Start

Follow these steps to enable budget alerts with email notifications:

### Step 1: Install Dependencies

If not already installed, install Flask-Mail:

```bash
# If using Docker (recommended)
docker-compose down
docker-compose build
docker-compose up -d

# If running locally
pip install -r requirements.txt
```

### Step 2: Configure Email

1. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file with your SMTP settings:**

   **For Gmail (most common):**
   ```bash
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=true
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   MAIL_DEFAULT_SENDER=noreply@fina.app
   APP_URL=http://localhost:5001
   ```

   **Get Gmail App Password:**
   1. Go to https://myaccount.google.com/security
   2. Enable 2-Step Verification
   3. Go to https://myaccount.google.com/apppasswords
   4. Create an app password for "Mail"
   5. Use this password in MAIL_PASSWORD

### Step 3: Run Database Migration

Add the new budget columns to your database:

```bash
# Using Docker
docker-compose exec web python migrations/migrate_budget_alerts.py

# Or locally
python migrations/migrate_budget_alerts.py
```

Expected output:
```
🔧 Starting budget alerts migration...

📊 Migrating Category table...
  ✓ Adding monthly_budget column
  ✓ Adding budget_alert_sent column
  ✓ Adding budget_alert_threshold column
  ✓ Adding last_budget_check column

👤 Migrating User table...
  ✓ Adding budget_alerts_enabled column
  ✓ Adding alert_email column

✅ Migration completed successfully!
```

### Step 4: Restart Application

```bash
# Docker
docker-compose restart

# Or locally
# Stop the app (Ctrl+C) and restart:
python wsgi.py
```

### Step 5: Enable Budget Alerts

**In the web interface:**

1. **Enable for your account:**
   - Go to Settings (top-right menu)
   - Scroll to "Budget Alert Settings"
   - Check "Enable budget alert emails"
   - (Optional) Enter a different email for alerts
   - Click "Save Changes"

2. **Set category budgets:**
   - Go to Dashboard
   - Click on any category
   - Click "Edit Category"
   - Scroll to "Budget Management"
   - Enter:
     - **Monthly Budget Limit**: e.g., 500
     - **Alert Threshold**: e.g., 100 (means notify at 100% of budget)
   - Click "Save Changes"

### Step 6: Test It!

**Option 1: Add expenses to trigger alert**
1. Add expenses to your budgeted category
2. When total exceeds the threshold, you'll receive an email

**Option 2: Test email function manually**

Open Python console:
```bash
# Docker
docker-compose exec web python

# Or locally
python
```

Run test:
```python
from app.budget_alerts import send_test_budget_alert
send_test_budget_alert('your-email@example.com')
```

Check your inbox for a test budget alert email!

## Troubleshooting

### Problem: Migration fails with "column already exists"

**Solution:** Migration already applied, skip this step.

### Problem: No emails being sent

**Check 1: SMTP Configuration**
```python
# In Python console
from app import create_app
app = create_app()
with app.app_context():
    print("MAIL_SERVER:", app.config.get('MAIL_SERVER'))
    print("MAIL_PORT:", app.config.get('MAIL_PORT'))
    print("MAIL_USERNAME:", app.config.get('MAIL_USERNAME'))
    print("MAIL_USE_TLS:", app.config.get('MAIL_USE_TLS'))
```

**Check 2: Test email sending**
```python
from app.budget_alerts import send_test_budget_alert
send_test_budget_alert('your-email@example.com')
```

**Check 3: Common issues**
- Gmail: Must use App Password, not account password
- Firewall: Port 587 must be open
- TLS: Make sure MAIL_USE_TLS=true
- Credentials: Verify username and password are correct

**Check 4: Application logs**
```bash
# Docker
docker-compose logs web

# Look for errors related to SMTP or email
```

### Problem: Alert sent but I don't see email

1. **Check spam folder**
2. **Verify alert_email in settings** (if set, email goes there instead)
3. **Check user settings**: Budget alerts must be enabled
4. **Check category budget**: Must have monthly_budget set

### Problem: Multiple alerts for same category

This shouldn't happen! The system tracks `budget_alert_sent` flag. If you're getting duplicates:

1. **Check database:**
   ```sql
   SELECT name, monthly_budget, budget_alert_sent, last_budget_check 
   FROM category 
   WHERE monthly_budget IS NOT NULL;
   ```

2. **Manually reset if needed:**
   ```sql
   UPDATE category SET budget_alert_sent = FALSE WHERE id = YOUR_CATEGORY_ID;
   ```

## Configuration Options

### Alert Threshold Examples

- **100%** - Alert when you hit your budget exactly ($500 budget → alert at $500)
- **80%** - Early warning ($500 budget → alert at $400)
- **150%** - Alert after overspending ($500 budget → alert at $750)
- **50%** - Very early warning ($500 budget → alert at $250)

### Email Providers

#### Gmail (Free)
- ✅ Easy to set up
- ✅ Reliable
- ❌ Requires App Password
- Limit: ~500 emails/day

#### SendGrid (Free tier)
- ✅ Professional service
- ✅ Good deliverability
- ✅ 100 emails/day free
```bash
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USERNAME=apikey
MAIL_PASSWORD=your-sendgrid-api-key
```

#### Mailgun (Free trial)
- ✅ Developer-friendly
- ✅ Good API
- ⚠️ Requires domain verification
```bash
MAIL_SERVER=smtp.mailgun.org
MAIL_PORT=587
MAIL_USERNAME=postmaster@your-domain.mailgun.org
MAIL_PASSWORD=your-mailgun-password
```

#### Amazon SES (Pay per use)
- ✅ Scalable
- ✅ Very reliable
- ❌ More complex setup
```bash
MAIL_SERVER=email-smtp.us-east-1.amazonaws.com
MAIL_PORT=587
MAIL_USERNAME=your-ses-username
MAIL_PASSWORD=your-ses-password
```

## How It Works

### Automatic Checks
- Budget is checked **every time you add an expense**
- No scheduled jobs needed - event-driven
- Smart monthly reset automatically

### Alert Logic
```
IF:
  - Category has monthly_budget set
  - Current spending ≥ (budget × threshold / 100)
  - budget_alert_sent = False (not sent this month yet)
  - User has budget_alerts_enabled = True
THEN:
  - Send email
  - Set budget_alert_sent = True
```

### Monthly Reset
At the start of each new month:
- `budget_alert_sent` resets to False
- New spending starts at $0
- Can receive new alert for that month

### Email Contents
Each alert email includes:
- Category name and icon
- Current spending amount
- Budget amount
- Percentage over budget
- Visual progress bar
- Link to view category
- Localized in your language (EN/RO/ES)

## Advanced Usage

### Multiple Budget Scenarios

**Scenario 1: Strict budgets (early warning)**
```
Food: $500 budget, 80% threshold = alert at $400
Transport: $200 budget, 80% threshold = alert at $160
```

**Scenario 2: Flexible budgets (alert when over)**
```
Entertainment: $300 budget, 150% threshold = alert at $450
Shopping: $400 budget, 120% threshold = alert at $480
```

### Separate Alert Email

Useful for:
- Shared family accounts (spouse gets alerts)
- Business expense tracking (accountant gets alerts)
- Forwarding to task management system

Setup:
1. Settings → Profile
2. Enter different email in "Alert Email"
3. Budget alerts go there, but you still login with main email

### Disable Alerts Temporarily

Want to stop getting alerts without removing budgets?

1. Settings → Profile
2. Uncheck "Enable budget alert emails"
3. Save

Budgets are still tracked, but no emails sent.

## Next Steps

After setup:
1. **Set budgets on main categories** (Food, Transport, Entertainment)
2. **Use 80-100% thresholds** for important categories
3. **Review monthly** - adjust budgets based on actual spending
4. **Check email logs** to see when alerts were sent
5. **Export data** to analyze budget vs. actual over time

## Support

Need help?
- Read [full documentation](../docs/BUDGET_ALERTS.md)
- Check [security audit](../docs/SECURITY_AUDIT.md)
- Open an issue on GitHub
- Check application logs for errors

---

**Remember:** Budget alerts help you stay on track, but they're not a substitute for regular financial review. Check your dashboard regularly!
