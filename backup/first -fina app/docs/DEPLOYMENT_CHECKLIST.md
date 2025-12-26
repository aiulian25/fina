# 🚀 Custom Recurring Expenses - Deployment Checklist

## Pre-Deployment

### 1. Code Review
- [x] Database model updated with 7 new fields
- [x] Routes handle custom interval input
- [x] Forms include custom frequency options
- [x] Templates display AUTO badge
- [x] Translations complete (EN, RO, ES)
- [x] Auto-create logic implemented
- [x] Occurrence counter working
- [x] JavaScript toggle for custom interval
- [x] No syntax errors found

### 2. Migration Prepared
- [x] Migration script created (`migrate_custom_recurring.py`)
- [x] Script is executable
- [x] Handles existing data gracefully
- [x] Backfills start_date from next_due_date
- [x] Backwards compatible

### 3. Documentation
- [x] Complete user guide (`CUSTOM_RECURRING_GUIDE.md`)
- [x] Feature summary (`CUSTOM_RECURRING_SUMMARY.md`)
- [x] Change log (`CUSTOM_RECURRING_CHANGES.md`)
- [x] Examples provided
- [x] Troubleshooting section

## Deployment Steps

### Step 1: Backup Database ⚠️
```bash
# Create backup before migration
docker run --rm \
  -v fina-db:/data \
  -v $(pwd):/backup \
  alpine cp /data/finance.db /backup/finance_backup_$(date +%Y%m%d_%H%M%S).db
```
**Expected**: `finance_backup_20251217_*.db` file created

### Step 2: Run Migration
```bash
# If using Docker
docker exec fina-web python migrate_custom_recurring.py

# If running locally
python migrate_custom_recurring.py
```
**Expected output**:
```
🔄 Adding custom recurring expense fields...
  ✅ Added column: custom_interval_days
  ✅ Added column: start_date
  ✅ Added column: end_date
  ✅ Added column: total_occurrences
  ✅ Added column: occurrences_count
  ✅ Added column: auto_create_expense
  ✅ Added column: last_auto_created

✅ Migration completed successfully!
```

### Step 3: Restart Application
```bash
# Docker
docker compose restart

# Or full rebuild
docker compose down
docker compose build
docker compose up -d
```
**Expected**: Containers restart without errors

### Step 4: Verify Migration
```bash
# Check database schema
docker exec fina-web python -c "
from app import create_app, db
from app.models.subscription import Subscription

app = create_app()
with app.app_context():
    # Check table structure
    print('Subscription columns:')
    for column in Subscription.__table__.columns:
        print(f'  - {column.name}: {column.type}')
"
```
**Expected**: All 7 new columns listed

## Post-Deployment Testing

### Test 1: Create Standard Subscription ✓
1. Navigate to `/subscriptions`
2. Click "➕ Add Subscription"
3. Fill form with monthly frequency
4. Save

**Expected**: Subscription created, no errors

### Test 2: Create Custom Interval ✓
1. Navigate to `/subscriptions/create`
2. Select "Custom" from frequency
3. Enter "45" in custom interval field
4. Save

**Expected**: 
- Custom interval field appears when Custom selected
- Subscription shows "Every 45 days"
- Next payment calculated correctly

### Test 3: Enable Auto-Create ✓
1. Create subscription
2. Check "Auto-Create Expenses"
3. Save
4. Click "⚡ Create Due Expenses" button

**Expected**: 
- AUTO badge appears
- Button creates expense if due today
- No duplicate expenses created

### Test 4: Set End Date ✓
1. Create subscription
2. Set end date to future date
3. Manually advance next_due_date past end_date
4. Check subscription status

**Expected**: Subscription becomes inactive after end date

### Test 5: Total Occurrences ✓
1. Create subscription with total_occurrences = 3
2. Trigger auto-create 3 times
3. Check subscription status

**Expected**: 
- Counter shows 3/3
- Subscription becomes inactive
- No more expenses created

### Test 6: Multi-Language ✓
1. Switch to Romanian
2. Navigate to subscriptions
3. Create subscription
4. Check all labels

**Expected**: All text in Romanian

1. Switch to Spanish
2. Repeat

**Expected**: All text in Spanish

### Test 7: Edit Existing Subscription ✓
1. Open old subscription (before migration)
2. Click Edit
3. Add custom features
4. Save

**Expected**: Updates work, backward compatible

### Test 8: Dashboard Widget ✓
1. Create subscription due soon
2. Navigate to dashboard
3. Check "Upcoming Subscriptions" widget

**Expected**: 
- Shows custom intervals correctly
- Displays AUTO badge
- Calculates days correctly

## Verification Queries

### Check Migration Success
```sql
-- Run in SQLite
sqlite3 instance/finance.db

-- Check new columns exist
PRAGMA table_info(subscriptions);

-- Should see:
-- custom_interval_days | INTEGER
-- start_date | DATE
-- end_date | DATE
-- total_occurrences | INTEGER
-- occurrences_count | INTEGER
-- auto_create_expense | BOOLEAN
-- last_auto_created | DATE
```

### Check Data Integrity
```sql
-- Verify no NULL start_dates for active subscriptions
SELECT COUNT(*) FROM subscriptions 
WHERE is_active = 1 AND start_date IS NULL;
-- Expected: 0

-- Check auto-create subscriptions
SELECT name, auto_create_expense, occurrences_count, total_occurrences
FROM subscriptions
WHERE auto_create_expense = 1;
-- Expected: Shows auto-create subscriptions with counters
```

## Rollback Plan (If Needed)

### Emergency Rollback
```bash
# Stop application
docker compose down

# Restore backup
docker run --rm \
  -v fina-db:/data \
  -v $(pwd):/backup \
  alpine cp /backup/finance_backup_TIMESTAMP.db /data/finance.db

# Restart with old code
git checkout previous_commit
docker compose up -d
```

### Partial Rollback (Keep Data)
New columns won't break anything - they're optional. App works without them.

## Monitoring

### Check Logs
```bash
# Docker logs
docker compose logs -f web

# Look for:
# - Migration success messages
# - No errors on subscription create/edit
# - Auto-create execution logs
```

### Key Metrics
- Subscriptions created with custom interval: Expected > 0
- Auto-create executions: Track success rate
- Errors: Expected = 0
- Translation loading: No missing keys

## Common Issues & Solutions

### Issue 1: Custom interval field not showing
**Cause**: JavaScript not loaded
**Solution**: Hard refresh (Ctrl+Shift+R), check console for errors

### Issue 2: Auto-create not working
**Cause**: next_due_date not set to today
**Solution**: Edit subscription, set next payment to today

### Issue 3: Occurrence counter not incrementing
**Cause**: Auto-create not enabled or not running
**Solution**: Enable auto-create, click button to trigger

### Issue 4: Translation missing
**Cause**: Cache not cleared
**Solution**: Restart containers, clear browser cache

## Success Criteria

- [ ] Migration completed without errors
- [ ] All existing subscriptions still work
- [ ] Custom interval creates successfully
- [ ] Auto-create generates expenses
- [ ] Occurrence counter increments
- [ ] End date deactivates subscriptions
- [ ] Total occurrences limit works
- [ ] Romanian translations load
- [ ] Spanish translations load
- [ ] AUTO badge displays
- [ ] Dashboard shows custom intervals
- [ ] No console errors
- [ ] No Python errors in logs

## Post-Deployment Communication

### User Announcement
```
🎉 New Feature: Custom Recurring Expenses!

We've added powerful new features to subscription tracking:

✨ What's New:
- Create subscriptions with ANY custom interval (e.g., every 45 days)
- Set start and end dates for limited subscriptions
- Limit total number of payments
- Auto-create expenses on due date (no more manual logging!)
- Track occurrence count automatically

📚 Documentation:
- User Guide: CUSTOM_RECURRING_GUIDE.md
- Quick Start: CUSTOM_RECURRING_SUMMARY.md

🚀 Try it now:
1. Go to Subscriptions
2. Click "Add Subscription"
3. Select "Custom" frequency
4. Enable "Auto-Create Expenses"
5. Set it and forget it!

Questions? See the guide or contact support.
```

## Maintenance Notes

### Future Improvements
- [ ] Email notifications for upcoming payments
- [ ] SMS reminders (optional)
- [ ] Bulk import subscriptions
- [ ] Subscription categories
- [ ] Payment history per subscription
- [ ] Export subscription data (CSV)

### Known Limitations
- Auto-create requires manual button click (no automatic cron yet)
- End date doesn't send notification
- No prorated amounts for mid-cycle changes
- Maximum custom interval: 9999 days

### Optimization Opportunities
- Index on next_due_date for faster queries
- Cache upcoming subscriptions
- Batch auto-create operations
- Background job for auto-create (vs button click)

## Support Resources

- **User Guide**: [CUSTOM_RECURRING_GUIDE.md](CUSTOM_RECURRING_GUIDE.md)
- **Change Log**: [CUSTOM_RECURRING_CHANGES.md](CUSTOM_RECURRING_CHANGES.md)
- **Migration Script**: `migrate_custom_recurring.py`
- **Code**: 
  - Model: `app/models/subscription.py`
  - Routes: `app/routes/subscriptions.py`
  - Templates: `app/templates/subscriptions/*.html`

---

## Sign-Off

**Deployment Date**: _______________

**Deployed By**: _______________

**Verification Completed**: [ ] Yes [ ] No

**Issues Encountered**: _______________

**Rollback Required**: [ ] Yes [ ] No

**Status**: [ ] Success [ ] Failed [ ] Partial

**Notes**:
_______________________________________________
_______________________________________________
_______________________________________________

---

**Version**: Custom Recurring Expenses v1.0
**Compatibility**: FINA v2.0+
**Breaking Changes**: None
**Database Migration**: Required ✓
