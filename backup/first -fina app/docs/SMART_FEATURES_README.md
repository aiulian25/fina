# Smart Recurring Expense Detection & Subscription Management

## Overview
FINA now includes intelligent recurring expense detection that automatically identifies subscription patterns and suggests them to users. This feature helps users track and manage their recurring expenses more effectively.

## Features Implemented

### 1. **Smart Detection Algorithm**
- Analyzes expense history to find recurring patterns
- Detects frequencies: Weekly, Bi-weekly, Monthly, Quarterly, Yearly
- Considers:
  - **Amount similarity** (5% tolerance)
  - **Description matching** (fuzzy matching)
  - **Time intervals** (consistent payment dates)
  - **Category grouping** (same category)
- Generates **confidence score** (0-100%) for each detection
- Minimum 3 occurrences required for pattern detection

### 2. **Subscription Management**
- **Track active subscriptions** with payment schedules
- **Add subscriptions manually** or accept AI suggestions
- **View total costs** (monthly and yearly)
- **Pause/Resume subscriptions** without deleting
- **Upcoming payments** widget on dashboard
- **Notes field** for additional context

### 3. **Smart Suggestions**
- AI-detected patterns shown as suggestions
- **Confidence score** indicates reliability
- Shows occurrence count and time period
- **Accept** to convert to subscription
- **Dismiss** to hide unwanted suggestions
- Visual indicators for high-confidence matches

### 4. **Dashboard Integration**
- **Upcoming subscriptions** widget (next 30 days)
- **Notification badge** for new suggestions
- Quick link to subscription management
- Real-time payment reminders

## Usage

### Running Detection
1. Navigate to **Subscriptions** page
2. Click **🔍 Detect Recurring** button
3. Algorithm analyzes your expense history
4. Suggestions appear with confidence scores

### Managing Suggestions
- **✅ Accept**: Converts pattern to tracked subscription
- **❌ Dismiss**: Hides the suggestion
- View details: Amount, frequency, occurrences, time range

### Adding Subscriptions
- **Manual Entry**: Click "➕ Add Subscription"
- Fill in: Name, Amount, Frequency, Category, Next Payment Date
- Add optional notes

### Tracking Payments
- View all active subscriptions
- See monthly and annual costs
- Check upcoming payment dates
- Edit or pause anytime

## API Endpoints

### `/subscriptions/detect` (POST)
Runs detection algorithm for current user

### `/subscriptions/api/upcoming` (GET)
Returns upcoming subscriptions as JSON
- Query param: `days` (default: 30)

### `/subscriptions/suggestion/<id>/accept` (POST)
Converts detected pattern to subscription

### `/subscriptions/suggestion/<id>/dismiss` (POST)
Dismisses a suggestion

## Detection Algorithm Details

### Pattern Matching
```python
# Amount tolerance: 5% or $5 (whichever is larger)
tolerance = max(amount * 0.05, 5.0)

# Description normalization
- Removes dates, transaction numbers
- Lowercases and strips whitespace
- Checks word overlap (60% threshold)

# Interval analysis
- Calculates average days between transactions
- Checks variance (lower = higher confidence)
- Maps to standard frequencies
```

### Confidence Scoring
Base confidence starts at 50-70% depending on interval consistency:
- **+15%** for monthly patterns (most common)
- **+10%** for weekly patterns
- **+10%** if amount variance < 5%
- **-10%** if amount variance > 20%
- **-10%** for less common intervals

## Database Schema

### Subscriptions Table
- `name`: Subscription name (e.g., "Netflix")
- `amount`: Payment amount
- `frequency`: weekly | biweekly | monthly | quarterly | yearly
- `category_id`: Linked category
- `next_due_date`: Next payment date
- `is_active`: Active/paused status
- `is_confirmed`: User confirmed (vs AI suggestion)
- `auto_detected`: Created from AI detection
- `confidence_score`: Detection confidence (0-100)
- `notes`: User notes

### Recurring Patterns Table
- Stores detected patterns before user confirmation
- Links to original expense IDs (JSON array)
- Tracks acceptance/dismissal status
- Prevents duplicate suggestions

## Multi-Language Support
All subscription features fully translated:
- 🇬🇧 English
- 🇷🇴 Romanian  
- 🇪🇸 Spanish

Translation keys added:
- `subscription.*` - All subscription-related text
- Frequency labels (weekly, monthly, etc.)
- Dashboard widgets
- Action buttons

## Best Practices

### For Users
1. **Add expenses regularly** - More data = better detection
2. **Use consistent descriptions** - Helps pattern matching
3. **Run detection monthly** - Catch new subscriptions
4. **Review suggestions carefully** - Check confidence scores
5. **Add notes** - Remember renewal terms, cancellation dates

### For Developers
1. **Run detection as background job** - Don't block UI
2. **Cache detection results** - Expensive operation
3. **Adjust confidence thresholds** - Based on user feedback
4. **Monitor false positives** - Track dismissal rates
5. **Extend pattern types** - Add custom frequencies

## Future Enhancements
- Email/push notifications for upcoming payments
- Category-based insights (subscription spending)
- Price change detection
- Cancellation reminders
- Bulk operations
- Export subscription list
- Recurring expense auto-entry
- Integration with calendar apps

## Testing
```bash
# Rebuild with new models
docker compose down
docker compose up --build -d

# Access app
http://localhost:5001/subscriptions

# Test detection
1. Add similar expenses (3+) with regular intervals
2. Click "Detect Recurring"
3. Check suggestions appear with confidence scores
4. Accept or dismiss suggestions
5. View on dashboard
```

## Troubleshooting

**No patterns detected:**
- Need minimum 3 similar transactions
- Check amount similarity (within 5%)
- Ensure consistent time intervals
- Verify same category used

**Low confidence scores:**
- Irregular payment dates
- Varying amounts
- Different descriptions
- Try manual entry instead

**Missing upcoming payments:**
- Check `next_due_date` is set
- Verify subscription is active
- Ensure date within 30 days

## Architecture
```
User Actions
    ↓
Routes (subscriptions.py)
    ↓
Smart Detection (smart_detection.py)
    ↓
Models (subscription.py)
    ↓
Database (SQLite)
```

Pattern detection is stateless and can run independently. Results stored in `recurring_patterns` table until user action.
