# 🔄 Custom Recurring Expenses - Complete Guide

## Overview

The Custom Recurring Expenses feature gives you complete control over how you track and manage recurring payments. Unlike basic subscriptions, you can now:

- Set **custom intervals** (e.g., every 45 days, every 3 days)
- Define **start and end dates** for limited subscriptions
- Limit **total number of payments**
- **Auto-create expenses** when payments are due
- Track occurrence count automatically

## 🎯 Use Cases

### 1. Unusual Payment Schedules
Some services don't fit standard weekly/monthly cycles:
- Quarterly payments that occur every 90 days
- Bi-monthly payments (every 60 days)
- Custom service contracts (e.g., every 45 days)

**Solution**: Use "Custom" frequency and specify exact days

### 2. Limited-Time Subscriptions
Gym memberships, trial periods, or fixed-term contracts:
- 12-month gym membership
- 6-month software trial
- Fixed payment plans

**Solution**: Set "Total Payments" to limit occurrences

### 3. Automatic Expense Creation
Tired of manually adding recurring expenses each month?
- Rent payments
- Utility bills
- Subscription services

**Solution**: Enable "Auto-Create Expenses" feature

### 4. Temporary Subscriptions
Services you'll cancel after a specific date:
- Seasonal subscriptions (summer streaming service)
- Short-term rentals
- Project-based services

**Solution**: Set "End Date" to automatically deactivate

## 📋 Features Explained

### Custom Frequency Interval

**What it is**: Define recurring payments with any interval (in days)

**How to use**:
1. Select "Custom" from frequency dropdown
2. Enter number of days between payments
3. Examples:
   - Every 45 days
   - Every 10 days
   - Every 3 days

**Formula**: Next payment = Last payment + interval days

### Start Date

**What it is**: First occurrence date of the subscription

**How to use**:
- Defaults to today
- Change to past date to track existing subscriptions
- Change to future date to schedule upcoming subscriptions

**Behavior**: Next payment is calculated from this date

### End Date (Optional)

**What it is**: Date when subscription automatically stops

**How to use**:
- Leave blank for ongoing subscriptions
- Set date for temporary subscriptions
- Subscription becomes inactive after this date

**Example**: 
- Gym membership ends Dec 31, 2025
- Summer streaming service ends Sep 1

### Total Payments (Optional)

**What it is**: Maximum number of payments before subscription ends

**How to use**:
- Leave blank for unlimited payments
- Enter number for fixed-term contracts
- Tracks automatically with "Remaining" counter

**Example**:
- 12-month payment plan (12 payments)
- 6-month trial (6 payments)

**Behavior**: Subscription becomes inactive after reaching limit

### Auto-Create Expenses ⚡

**What it is**: Automatically creates expenses when payment is due

**How to use**:
1. Check "Auto-Create Expenses" box
2. Click "⚡ Create Due Expenses" button on subscription page
3. Or run manually: POST to `/subscriptions/auto-create`

**Automation Options**:
- **Manual**: Click button when you want to check
- **Scheduled**: Set up cron job (see below)
- **Daily Login**: Click on first daily visit

**Created Expense Details**:
- Amount: Same as subscription
- Description: "[Name] (Auto-created)"
- Date: Today
- Category: Same as subscription

**Safety Features**:
- Only creates once per day
- Respects total occurrence limits
- Respects end dates
- Shows remaining payments counter

## 🚀 Quick Start Examples

### Example 1: Netflix Subscription (Standard)
```
Name: Netflix Premium
Amount: $19.99
Frequency: Monthly
Start Date: Jan 1, 2025
End Date: (blank - ongoing)
Auto-Create: ✓ Checked
```

### Example 2: Gym Membership (Limited Term)
```
Name: Gym Membership
Amount: $50.00
Frequency: Monthly
Start Date: Jan 1, 2025
End Date: Dec 31, 2025
Total Payments: 12
Auto-Create: ✓ Checked
```

### Example 3: Car Maintenance (Custom Interval)
```
Name: Oil Change
Amount: $75.00
Frequency: Custom
Custom Interval: 90 days
Start Date: Jan 15, 2025
Total Payments: 4 (yearly)
Auto-Create: (unchecked - manual)
```

### Example 4: Medication Refill (Short Interval)
```
Name: Prescription Refill
Amount: $25.00
Frequency: Custom
Custom Interval: 30 days
Start Date: Today
Total Payments: 6
Auto-Create: ✓ Checked
```

## 🤖 Auto-Create Setup

### Manual Trigger
Visit Subscriptions page and click "⚡ Create Due Expenses"

### Cron Job (Linux/Docker)
Add to crontab for daily execution at 9 AM:
```bash
0 9 * * * docker exec fina-web python -c "from app import create_app; from app.models.subscription import Subscription; from app.models.category import Expense; from app import db; app = create_app(); with app.app_context(): [app logic here]"
```

### Python Script (Simplified)
```python
#!/usr/bin/env python3
from app import create_app
from app.models.subscription import Subscription
from app.models.category import Expense
from app import db
from datetime import datetime

app = create_app()

with app.app_context():
    subscriptions = Subscription.query.filter_by(
        auto_create_expense=True,
        is_active=True
    ).all()
    
    for sub in subscriptions:
        if sub.should_create_expense_today():
            expense = Expense(
                amount=sub.amount,
                description=f"{sub.name} (Auto-created)",
                date=datetime.now().date(),
                category_id=sub.category_id,
                user_id=sub.user_id
            )
            db.session.add(expense)
            sub.last_auto_created = datetime.now().date()
            sub.advance_next_due_date()
    
    db.session.commit()
```

### Docker Compose Integration
Add to your `docker-compose.yml`:
```yaml
services:
  scheduler:
    image: your-app-image
    command: python scheduler.py
    environment:
      - RUN_SCHEDULER=true
    volumes:
      - ./instance:/app/instance
```

## 📊 Dashboard Integration

### Upcoming Payments Widget
Shows next 30 days of payments on dashboard:
- Subscription name
- Amount
- Days until due
- ⚡ AUTO badge for auto-create enabled

### Sorting
- By due date (ascending)
- Shows closest payments first
- Highlights overdue (if any)

## 🔍 Detection vs Manual

| Feature | AI Detected | Manual Entry |
|---------|------------|--------------|
| Source | Analyzed from expenses | User input |
| Confidence Score | 0-100% | N/A |
| Requires Confirmation | Yes | Pre-confirmed |
| Customization | Limited | Full control |
| Auto-Create | After confirmation | Available immediately |

**Workflow**:
1. AI detects recurring pattern → Suggestion
2. Review confidence score and pattern
3. Accept → Creates subscription with detection data
4. Edit → Add custom features (end date, auto-create, etc.)

## 🎨 UI Indicators

### Badges
- **⚡ AUTO**: Auto-create enabled
- **🔍 SUGGESTED**: AI-detected, pending confirmation
- **✓**: Confirmed by user

### Status Colors
- **Green (Active)**: Currently active subscription
- **Gray (Inactive)**: Ended or reached limit
- **Orange (Pending)**: AI suggestion awaiting review

### Frequency Display
- **Standard**: "Monthly", "Weekly", "Yearly"
- **Custom**: "Every 45 days", "Every 10 days"

## ⚠️ Important Notes

### Timing
- Auto-create checks run when button is clicked
- Only creates expenses with due date = today
- Won't create duplicate expenses (checks last_auto_created)

### Limits
- Total occurrences decrements automatically
- End date checked before creating expense
- Subscription auto-deactivates when limit reached

### Editing Active Subscriptions
- Changing frequency doesn't affect existing expenses
- Changing amount doesn't affect past expenses
- Next due date updates immediately

### Deleting Subscriptions
- Deletes subscription record only
- Does NOT delete associated expenses
- Cannot be undone

## 🐛 Troubleshooting

### Auto-Create Not Working
**Check**:
1. ✓ Auto-create checkbox enabled?
2. ✓ Subscription is active?
3. ✓ Today matches next_due_date?
4. ✓ Already created today? (check last_auto_created)
5. ✓ Within occurrence limits?
6. ✓ Before end date?

### Wrong Next Due Date
**Solution**: Edit subscription and manually set next payment date

### Custom Interval Not Showing
**Issue**: Frequency not set to "Custom"
**Solution**: Select "Custom" from dropdown first

### Occurrence Count Not Updating
**Issue**: Auto-create may not be enabled or not running
**Solution**: Each auto-created expense should increment count automatically

## 📱 Multi-Language Support

All features fully translated in:
- 🇬🇧 English
- 🇷🇴 Romanian (Română)
- 🇪🇸 Spanish (Español)

Translation keys include:
- `subscription.freq_custom`
- `subscription.custom_interval`
- `subscription.auto_create`
- `subscription.every`
- And 10+ more custom keys

## 🔐 Security

- User authentication required for all actions
- Subscriptions tied to user accounts
- Cannot view/edit other users' subscriptions
- CSRF protection on all forms

## 📈 Statistics

Track your spending patterns:
- Annual cost per subscription
- Total active subscriptions
- Average monthly spend
- Upcoming 30-day total

Formula: Annual Cost = (365 / interval_days) × amount

## 🎯 Best Practices

1. **Start Simple**: Begin with standard frequencies
2. **Test Auto-Create**: Try with one subscription first
3. **Set Realistic Limits**: Use total occurrences for known term lengths
4. **Review Regularly**: Check upcoming payments weekly
5. **Update Amounts**: Edit when prices change
6. **Archive Old**: Delete completed subscriptions
7. **Use Categories**: Organize by type (Bills, Entertainment, Health)

## 🚀 Migration

Run the migration script to enable these features:
```bash
python migrate_custom_recurring.py
```

Or let Docker handle it automatically:
```bash
./migrate_smart_features.sh
```

## 📝 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/subscriptions` | GET | List all subscriptions |
| `/subscriptions/create` | GET/POST | Add subscription form |
| `/subscriptions/<id>/edit` | GET/POST | Edit subscription |
| `/subscriptions/<id>/delete` | POST | Delete subscription |
| `/subscriptions/auto-create` | POST | Trigger auto-creation |
| `/subscriptions/api/upcoming` | GET | JSON list of upcoming |

## 💡 Tips & Tricks

1. **Quarterly Payments**: Use Custom → 90 days
2. **Bi-annual**: Use Custom → 182 days
3. **Weekly on Fridays**: Weekly + set start to Friday
4. **Rent (1st of month)**: Monthly + next_due_date = next 1st
5. **Payday Loans**: Custom interval matching pay schedule

## 📚 Related Features

- **PWA Support**: Add to phone, get offline access
- **Multi-Language**: Switch language in nav menu
- **Smart Detection**: AI suggests recurring patterns
- **Dashboard Widget**: See upcoming at a glance

---

**Version**: 1.0
**Last Updated**: December 2025
**Compatibility**: FINA v2.0+
