# Smart Tags System - User Guide

## Overview
The Smart Tags System has been successfully implemented in your financial tracking PWA. This feature automatically suggests relevant tags for expenses based on their description, category, and OCR text from receipts.

## What's New

### 1. **Complete Category Display**
- When adding an expense, ALL categories are now displayed in the dropdown
- This includes:
  - Default categories (Food & Dining, Transportation, Shopping, etc.)
  - Categories imported from CSV files
  - Categories auto-created from OCR receipt processing
  - Custom categories you've created

### 2. **Smart Tag Suggestions**
As you type the expense description, the system automatically suggests relevant tags:

**Example Suggestions:**
- "Coffee at Starbucks" → #dining, #coffee
- "Gas station fill up" → #gas
- "Grocery shopping at Walmart" → #groceries
- "Doctor appointment" → #medical
- "Monthly rent payment" → #subscription
- "Pizza delivery" → #dining

### 3. **Real-Time Tag Recommendations**
- Type at least 3 characters in the description field
- Smart suggestions appear below the description input
- Click any suggested tag to add it to your expense
- Tags are color-coded with icons for easy identification

### 4. **Auto-Tagging from OCR**
When you upload a receipt:
- OCR extracts text from the image
- The system analyzes the text
- Automatically suggests tags based on merchant names, keywords, and categories
- You can accept or modify the suggestions

## How to Use

### Adding an Expense with Tags

1. **Click "Add Expense" button**
2. **Fill in the amount and date**
3. **Start typing the description** (e.g., "Coffee at...")
   - After 3 characters, smart tag suggestions appear
4. **Select a category** from the dropdown
   - All your categories are listed
5. **Click suggested tags** to add them
   - Or manually type tags in the "Tags" field (comma-separated)
6. **Upload a receipt** (optional)
   - OCR will extract text and suggest additional tags
7. **Click "Save Expense"**

### Tag Format
- Tags are lowercase with hyphens (e.g., `#online-shopping`)
- Multiple tags are comma-separated: `coffee, dining, work`
- The # symbol is added automatically in the UI

## Smart Tag Patterns

The system recognizes 30+ predefined patterns including:

### 🍽️ Food & Dining
- restaurant, cafe, coffee, starbucks, mcdonald's, pizza, burger, food

### 🚗 Transportation
- gas, fuel, uber, lyft, taxi, parking, metro, bus

### 🛒 Shopping
- amazon, walmart, target, groceries, supermarket, online shopping

### 🎬 Entertainment
- movie, cinema, netflix, spotify, concert, theater

### 🏥 Healthcare
- pharmacy, doctor, hospital, clinic, medical, dentist

### 💡 Utilities
- electric, electricity, water, gas bill, internet, wifi

### 🏠 Housing
- rent, mortgage, lease

### 📚 Education
- school, university, college, course, tuition

## API Endpoints

### Get Tag Suggestions
```
POST /api/expenses/suggest-tags
{
  "description": "Coffee at Starbucks",
  "category_id": 1,
  "ocr_text": ""
}
```

**Response:**
```json
{
  "success": true,
  "suggested_tags": [
    {
      "name": "dining",
      "color": "#10b981",
      "icon": "restaurant"
    },
    {
      "name": "coffee",
      "color": "#8b4513",
      "icon": "local_cafe"
    }
  ],
  "existing_tags": [...]
}
```

### Get All Categories
```
GET /api/expenses/categories
```

**Response:**
```json
{
  "categories": [
    {
      "id": 1,
      "name": "Food & Dining",
      "color": "#10b981",
      "icon": "restaurant"
    },
    ...
  ],
  "popular_tags": [
    {
      "name": "coffee",
      "use_count": 15,
      "color": "#8b4513",
      "icon": "local_cafe"
    },
    ...
  ]
}
```

## Technical Details

### Files Modified
1. **app/templates/dashboard.html** - Added IDs to form fields and placeholder text
2. **app/static/js/dashboard.js** - Implemented real-time tag suggestions
3. **app/routes/expenses.py** - Added `/suggest-tags` endpoint
4. **app/auto_tagger.py** - Smart tagging engine with 30+ patterns

### Database Tables
- `tags` - Stores all tags with name, color, icon, and usage count
- `expense_tags` - Junction table linking expenses to tags
- Indexes on user_id, tag_id, expense_id for performance

### Security
- All tag operations are user-scoped (user_id filtering)
- Category validation ensures users can only tag their own expenses
- Input sanitization for tag names (alphanumeric + hyphens/underscores)

## Multi-Language Support

The Smart Tags feature is fully translated in:
- 🇬🇧 English
- 🇷🇴 Romanian

Translation keys include:
- `tags.suggestedTags` - "Suggested Tags"
- `tags.add` - "Add Tag"
- `tags.autoTagging` - "Auto Tagging"
- And 40+ more...

## Browser Compatibility

Works in all modern browsers:
- ✅ Chrome/Edge (recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers (PWA optimized)

## What's Next?

The Smart Tags system is fully functional! Future enhancements could include:
- Custom tag pattern training
- Tag analytics and insights
- Bulk tag operations
- Tag-based budgeting
- Smart tag recommendations based on spending history

## Testing Status

✅ Backend auto-tagging engine tested
✅ Tag suggestion API endpoint verified
✅ All 20 categories loading (including CSV imports)
✅ Real-time suggestion UI implemented
✅ Multi-language support added
✅ Security validation complete

## Questions?

The system is ready to use! Just add an expense and start typing to see the magic happen. 🚀
