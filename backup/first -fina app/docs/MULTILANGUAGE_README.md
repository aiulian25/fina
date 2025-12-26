# Multi-Language Support Implementation

## Overview
FINA now supports three languages:
- 🇬🇧 **English** (en)
- 🇷🇴 **Romanian** (ro)  
- 🇪🇸 **Spanish** (es)

## Features Added

### 1. Translation System
- Created `app/translations.py` with complete translation dictionaries
- 250+ translation keys covering all app sections
- Includes navigation, dashboard, categories, expenses, authentication, settings, and more

### 2. User Language Preference
- Added `language` field to User model (stores: en, ro, es)
- Language persists across sessions
- Defaults to English for new users

### 3. Language Switcher
- Flag-based dropdown in navigation bar (🇬🇧 🇷🇴 🇪🇸)
- Instantly switches language without page reload redirect
- Accessible from any page when logged in

### 4. Template Integration
- Global `_()` function available in all templates
- Automatic language detection from user profile
- Templates updated with translation keys

### 5. Settings Integration
- Language selector in Edit Profile page
- Shows flag emoji + language name
- Updates immediately on save

## Usage

### For Users
1. **Login** to your account
2. **Click the flag icon** (🇬🇧) in the navigation bar
3. **Select your preferred language** from the dropdown
4. The entire app will switch to that language

Alternatively:
1. Go to **Settings**
2. Click **Profile** 
3. Select language from dropdown
4. Click **Save Changes**

### For Developers

**Adding new translations:**
```python
# In app/translations.py, add to each language dict:
translations = {
    'en': {
        'new.key': 'English text',
    },
    'ro': {
        'new.key': 'Textul românesc',
    },
    'es': {
        'new.key': 'Texto en español',
    }
}
```

**Using in templates:**
```html
<!-- Simple translation -->
<h1>{{ _('dashboard.title') }}</h1>

<!-- In attributes -->
<button>{{ _('common.save') }}</button>

<!-- Mixed content -->
<p>{{ _('message.login_success') }}</p>
```

**Using in Python routes:**
```python
from app.translations import get_translation
from flask_login import current_user

# Get user's language
lang = current_user.language or 'en'

# Translate
message = get_translation('message.success', lang)
flash(message, 'success')
```

## Database Migration

**IMPORTANT:** Existing users need a database migration:

```bash
# Stop the app
docker compose down

# Backup database
docker run --rm -v fina-db:/data -v $(pwd):/backup alpine cp /data/finance.db /backup/finance_backup.db

# Restart app (will auto-migrate)
docker compose up -d
```

The app will automatically add the `language` column with default value 'en'.

## Translation Coverage

All major sections translated:
- ✅ Navigation & Menus
- ✅ Dashboard & Statistics
- ✅ Categories & Expenses
- ✅ Authentication (Login/Register/2FA)
- ✅ Settings & Profile
- ✅ User Management
- ✅ Import/Export
- ✅ PWA Install Prompts
- ✅ Error Messages
- ✅ Month Names
- ✅ Form Labels & Buttons

## Adding More Languages

To add a new language (e.g., French):

1. Add translation dictionary in `app/translations.py`:
```python
'fr': {
    'nav.new_category': 'Nouvelle Catégorie',
    # ... all other keys
}
```

2. Update `get_available_languages()`:
```python
{'code': 'fr', 'name': 'Français', 'flag': '🇫🇷'}
```

3. Update language switcher in `base.html`
4. Rebuild and restart!

## Notes
- Language preference stored per user
- No performance impact (pure Python dictionaries)
- Falls back to English if key missing
- Works offline (no API calls)
- Compatible with existing PWA features
