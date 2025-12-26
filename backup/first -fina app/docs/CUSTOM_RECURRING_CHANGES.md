# Custom Recurring Expenses - What Changed

## Database Model Changes

### Before
```python
class Subscription(db.Model):
    id
    name
    amount
    frequency  # only: weekly, biweekly, monthly, quarterly, yearly
    category_id
    user_id
    next_due_date
    is_active
    is_confirmed
    auto_detected
    confidence_score
    notes
    created_at
    last_reminded
```

### After ✨
```python
class Subscription(db.Model):
    id
    name
    amount
    frequency  # NOW INCLUDES: custom
    custom_interval_days  # 🆕 For custom frequency
    category_id
    user_id
    next_due_date
    start_date  # 🆕 First occurrence
    end_date  # 🆕 Optional end date
    total_occurrences  # 🆕 Payment limit
    occurrences_count  # 🆕 Current count
    is_active
    is_confirmed
    auto_detected
    auto_create_expense  # 🆕 Auto-creation flag
    confidence_score
    notes
    created_at
    last_reminded
    last_auto_created  # 🆕 Last auto-create date
    
    # 🆕 NEW METHODS
    should_create_expense_today()
    advance_next_due_date()
```

## Form Changes

### Create Subscription - Before
```html
Name: [_____]
Amount: [_____]
Frequency: [Monthly ▼]  ← Only 5 options
Category: [Bills ▼]
Next Payment: [2025-01-15]
Notes: [_________]

[Cancel] [Save]
```

### Create Subscription - After ✨
```html
Name: [_____]
Amount: [_____]
Frequency: [Custom ▼]  ← 6 options now, including Custom
    → Custom Interval: [45] days  🆕 (shown when Custom selected)
    
Category: [Bills ▼]

Start Date: [2025-01-01]  🆕
End Date: [2025-12-31]  🆕 (optional)
Total Payments: [12]  🆕 (optional)

☑ Auto-Create Expenses  🆕
  "Automatically add expense when payment is due"

Notes: [_________]

[Cancel] [Save]
```

## UI Display Changes

### Subscription List - Before
```
🔄 Netflix Premium
   💰 $19.99 / Monthly
   📅 Next: Jan 15, 2025
   📊 Annual: $239.88
   [Edit] [Delete]
```

### Subscription List - After ✨
```
🔄 Netflix Premium                      ⚡ AUTO  🆕
   💰 $19.99 / Monthly
   📅 Next: Jan 15, 2025
   📊 Annual: $239.88
   🔢 8/12 times  🆕 (if total_occurrences set)
   [Edit] [Delete]

🔄 Car Maintenance
   💰 $75.00 / Every 45 days  🆕 (custom interval display)
   📅 Next: Feb 28, 2025
   📊 Annual: $608.25
   [Edit] [Delete]
```

## Page Header Changes

### Before
```
🔄 Subscriptions

[🔍 Detect Recurring] [➕ Add Subscription]
```

### After ✨
```
🔄 Subscriptions

[⚡ Create Due Expenses]  🆕  [🔍 Detect Recurring] [➕ Add Subscription]
```

## Route Changes

### Before
```python
GET  /subscriptions           # List
GET  /subscriptions/create    # Form
POST /subscriptions/create    # Save
GET  /subscriptions/<id>/edit # Edit form
POST /subscriptions/<id>/edit # Update
POST /subscriptions/<id>/delete
POST /subscriptions/detect    # AI detection
POST /subscriptions/<id>/accept
POST /subscriptions/<id>/dismiss
GET  /subscriptions/api/upcoming
```

### After ✨
```python
GET  /subscriptions           # List
GET  /subscriptions/create    # Form (now with custom fields)
POST /subscriptions/create    # Save (handles custom data)
GET  /subscriptions/<id>/edit # Edit form (now with custom fields)
POST /subscriptions/<id>/edit # Update (handles custom data)
POST /subscriptions/<id>/delete
POST /subscriptions/detect    # AI detection
POST /subscriptions/<id>/accept
POST /subscriptions/<id>/dismiss
GET  /subscriptions/api/upcoming
POST /subscriptions/auto-create  # 🆕 Auto-create expenses
```

## Translation Keys Added

### English
```python
'subscription.freq_custom': 'Custom'  🆕
'subscription.custom_interval': 'Repeat Every (Days)'  🆕
'subscription.start_date': 'Start Date'  🆕
'subscription.end_date': 'End Date'  🆕
'subscription.total_occurrences': 'Total Payments'  🆕
'subscription.auto_create': 'Auto-Create Expenses'  🆕
'subscription.create_due': 'Create Due Expenses'  🆕
'subscription.auto': 'AUTO'  🆕
'subscription.every': 'Every'  🆕
'subscription.days': 'days'  🆕
'subscription.times': 'times'  🆕
# + 5 more helper keys
```

### Romanian + Spanish
- All keys translated in both languages ✓

## Code Logic Changes

### Frequency Calculation - Before
```python
def get_frequency_days(self):
    frequency_map = {
        'weekly': 7,
        'biweekly': 14,
        'monthly': 30,
        'quarterly': 90,
        'yearly': 365
    }
    return frequency_map.get(self.frequency, 30)
```

### Frequency Calculation - After ✨
```python
def get_frequency_days(self):
    if self.frequency == 'custom' and self.custom_interval_days:  🆕
        return self.custom_interval_days  🆕
    
    frequency_map = {
        'weekly': 7,
        'biweekly': 14,
        'monthly': 30,
        'quarterly': 90,
        'yearly': 365
    }
    return frequency_map.get(self.frequency, 30)
```

### New Auto-Create Logic ✨
```python
def should_create_expense_today(self):
    """Check if expense should be auto-created today"""
    if not self.auto_create_expense or not self.is_active:
        return False
    
    if not self.next_due_date or self.next_due_date != today:
        return False
    
    if self.last_auto_created == today:
        return False  # Already created today
    
    if self.total_occurrences and self.occurrences_count >= self.total_occurrences:
        return False  # Reached limit
    
    if self.end_date and today > self.end_date:
        return False  # Past end date
    
    return True

def advance_next_due_date(self):
    """Move to next due date and check limits"""
    interval_days = self.get_frequency_days()
    self.next_due_date = self.next_due_date + timedelta(days=interval_days)
    self.occurrences_count += 1
    
    # Auto-deactivate if limits reached
    if self.total_occurrences and self.occurrences_count >= self.total_occurrences:
        self.is_active = False
    
    if self.end_date and self.next_due_date > self.end_date:
        self.is_active = False
```

## JavaScript Changes

### Create Form - Added
```javascript
function toggleCustomInterval() {
    const frequency = document.getElementById('frequency').value;
    const customGroup = document.getElementById('custom-interval-group');
    const customInput = document.getElementById('custom_interval_days');
    
    if (frequency === 'custom') {
        customGroup.style.display = 'block';
        customInput.required = true;
    } else {
        customGroup.style.display = 'none';
        customInput.required = false;
    }
}
```

## Files Created

1. `migrate_custom_recurring.py` - Migration script (Python)
2. `CUSTOM_RECURRING_GUIDE.md` - Complete user guide (30+ sections)
3. `CUSTOM_RECURRING_SUMMARY.md` - Quick feature summary

## Files Modified

1. `app/models/subscription.py` - Added 7 fields + 2 methods
2. `app/routes/subscriptions.py` - Updated create/edit + added auto-create endpoint
3. `app/templates/subscriptions/create.html` - Added custom frequency UI
4. `app/templates/subscriptions/edit.html` - Added custom frequency UI
5. `app/templates/subscriptions/index.html` - Added AUTO badge + auto-create button
6. `app/translations.py` - Added 15+ keys in 3 languages

## Migration Steps

### Database
```sql
-- New columns added:
ALTER TABLE subscriptions ADD COLUMN custom_interval_days INTEGER;
ALTER TABLE subscriptions ADD COLUMN start_date DATE;
ALTER TABLE subscriptions ADD COLUMN end_date DATE;
ALTER TABLE subscriptions ADD COLUMN total_occurrences INTEGER;
ALTER TABLE subscriptions ADD COLUMN occurrences_count INTEGER DEFAULT 0;
ALTER TABLE subscriptions ADD COLUMN auto_create_expense BOOLEAN DEFAULT 0;
ALTER TABLE subscriptions ADD COLUMN last_auto_created DATE;

-- Backfill start_date from next_due_date:
UPDATE subscriptions 
SET start_date = next_due_date 
WHERE start_date IS NULL AND next_due_date IS NOT NULL;
```

## Backward Compatibility

### ✅ Existing Subscriptions
- Continue working normally
- `custom_interval_days` is NULL (ignored)
- `auto_create_expense` defaults to False
- `start_date` backfilled from `next_due_date`

### ✅ Existing Routes
- All original routes still work
- New fields optional
- Forms handle NULL values gracefully

### ✅ API Responses
- New fields returned but not required
- Clients can ignore new fields
- No breaking changes

## Testing Scenarios

### ✅ Tested
1. Create standard monthly subscription → Works
2. Create custom 45-day interval → Works  
3. Enable auto-create → Works
4. Set end date → Deactivates correctly
5. Set total payments (12) → Counts properly
6. Edit existing subscription → Preserves data
7. Romanian translation → All keys present
8. Spanish translation → All keys present
9. Auto-create button → Creates expenses
10. Dashboard widget → Shows custom intervals

## Performance Impact

- **Database**: 7 new columns (minimal impact)
- **Queries**: No additional complexity
- **UI**: 1 additional button (negligible)
- **JavaScript**: 1 small function (< 1KB)
- **Translation**: 15 keys × 3 languages (< 2KB)

**Overall**: Negligible performance impact ✓

## Security Considerations

- All routes require `@login_required` ✓
- CSRF tokens on all forms ✓
- User-scoped queries only ✓
- Input validation on custom interval ✓
- SQL injection prevented (SQLAlchemy ORM) ✓

## Summary of Improvements

| Feature | Before | After | Improvement |
|---------|--------|-------|-------------|
| Frequency Options | 5 | 6 (+ custom) | +20% flexibility |
| Scheduling Control | Basic | Advanced | End dates, limits |
| Automation | Manual only | Auto-create | Time savings |
| Occurrence Tracking | None | Full counter | Better insights |
| Custom Intervals | No | Yes | Unlimited flexibility |

---

**Total Lines of Code Changed**: ~500 lines
**New Features Added**: 7 major features
**Languages Supported**: 3 (EN, RO, ES)
**Database Columns Added**: 7
**New Routes**: 1 (auto-create)
**Documentation Pages**: 2 comprehensive guides
