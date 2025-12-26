"""
Smart Auto-Tagging Utility
Automatically generates tags for expenses based on OCR text and description
"""
import re
from typing import List, Dict

# Tag patterns for auto-detection
TAG_PATTERNS = {
    # Food & Dining
    'dining': {
        'keywords': ['restaurant', 'cafe', 'bistro', 'diner', 'eatery', 'pizz', 'burger', 'sushi', 
                    'food court', 'takeout', 'delivery', 'uber eats', 'doordash', 'grubhub', 'postmates',
                    'restaurante', 'pizzeria', 'fast food', 'kfc', 'mcdonald', 'subway', 'starbucks'],
        'color': '#10b981',
        'icon': 'restaurant'
    },
    'groceries': {
        'keywords': ['supermarket', 'grocery', 'market', 'walmart', 'kroger', 'whole foods', 'trader joe',
                    'safeway', 'costco', 'aldi', 'lidl', 'carrefour', 'tesco', 'fresh', 'produce',
                    'kaufland', 'mega image', 'penny'],
        'color': '#22c55e',
        'icon': 'shopping_cart'
    },
    'coffee': {
        'keywords': ['coffee', 'starbucks', 'cafe', 'caffè', 'espresso', 'latte', 'cappuccino'],
        'color': '#92400e',
        'icon': 'coffee'
    },
    
    # Transportation
    'gas': {
        'keywords': ['gas station', 'fuel', 'petrol', 'shell', 'bp', 'exxon', 'chevron', 'mobil', 
                    'texaco', 'station', 'benzinarie', 'combustibil', 'petrom', 'omv', 'lukoil'],
        'color': '#ef4444',
        'icon': 'local_gas_station'
    },
    'parking': {
        'keywords': ['parking', 'garage', 'parcare', 'parcomat'],
        'color': '#f97316',
        'icon': 'local_parking'
    },
    'transport': {
        'keywords': ['uber', 'lyft', 'taxi', 'cab', 'bus', 'metro', 'train', 'subway', 'transit',
                    'bolt', 'autobuz', 'metrou', 'tren', 'ratb'],
        'color': '#3b82f6',
        'icon': 'directions_car'
    },
    
    # Shopping
    'online-shopping': {
        'keywords': ['amazon', 'ebay', 'aliexpress', 'online', 'emag', 'altex', 'flanco'],
        'color': '#a855f7',
        'icon': 'shopping_bag'
    },
    'clothing': {
        'keywords': ['clothing', 'fashion', 'apparel', 'zara', 'h&m', 'nike', 'adidas', 
                    'levi', 'gap', 'imbracaminte', 'haine'],
        'color': '#ec4899',
        'icon': 'checkroom'
    },
    'electronics': {
        'keywords': ['electronics', 'apple', 'samsung', 'sony', 'best buy', 'media markt'],
        'color': '#6366f1',
        'icon': 'devices'
    },
    
    # Entertainment
    'entertainment': {
        'keywords': ['movie', 'cinema', 'theater', 'concert', 'show', 'ticket', 'netflix', 'spotify',
                    'hbo', 'disney', 'entertainment', 'cinema city', 'teatru', 'concert'],
        'color': '#8b5cf6',
        'icon': 'movie'
    },
    'gym': {
        'keywords': ['gym', 'fitness', 'workout', 'sport', 'sala', 'world class'],
        'color': '#14b8a6',
        'icon': 'fitness_center'
    },
    
    # Bills & Utilities
    'electricity': {
        'keywords': ['electric', 'power', 'energie', 'enel', 'electrica'],
        'color': '#fbbf24',
        'icon': 'bolt'
    },
    'water': {
        'keywords': ['water', 'apa', 'aqua'],
        'color': '#06b6d4',
        'icon': 'water_drop'
    },
    'internet': {
        'keywords': ['internet', 'broadband', 'wifi', 'fiber', 'digi', 'upc', 'telekom', 'orange', 'vodafone'],
        'color': '#3b82f6',
        'icon': 'wifi'
    },
    'phone': {
        'keywords': ['phone', 'mobile', 'cellular', 'telefon', 'abonament'],
        'color': '#8b5cf6',
        'icon': 'phone_iphone'
    },
    'subscription': {
        'keywords': ['subscription', 'abonament', 'monthly', 'recurring'],
        'color': '#f59e0b',
        'icon': 'repeat'
    },
    
    # Healthcare
    'pharmacy': {
        'keywords': ['pharmacy', 'farmacie', 'drug', 'cvs', 'walgreens', 'catena', 'help net', 'sensiblu'],
        'color': '#ef4444',
        'icon': 'local_pharmacy'
    },
    'medical': {
        'keywords': ['doctor', 'hospital', 'clinic', 'medical', 'health', 'dental', 'spital', 'clinica'],
        'color': '#dc2626',
        'icon': 'medical_services'
    },
    
    # Other
    'insurance': {
        'keywords': ['insurance', 'asigurare', 'policy'],
        'color': '#64748b',
        'icon': 'shield'
    },
    'education': {
        'keywords': ['school', 'university', 'course', 'tuition', 'book', 'educatie', 'scoala', 'universitate'],
        'color': '#06b6d4',
        'icon': 'school'
    },
    'pet': {
        'keywords': ['pet', 'vet', 'veterinar', 'animal'],
        'color': '#f97316',
        'icon': 'pets'
    },
}


def extract_tags_from_text(text: str, max_tags: int = 5) -> List[Dict[str, str]]:
    """
    Extract relevant tags from OCR text or description
    
    Args:
        text: The text to analyze (OCR text or expense description)
        max_tags: Maximum number of tags to return
        
    Returns:
        List of tag dictionaries with name, color, and icon
    """
    if not text:
        return []
    
    # Normalize text: lowercase and remove special characters
    normalized_text = text.lower()
    normalized_text = re.sub(r'[^\w\s]', ' ', normalized_text)
    
    detected_tags = []
    
    # Check each pattern
    for tag_name, pattern_info in TAG_PATTERNS.items():
        for keyword in pattern_info['keywords']:
            # Use word boundary matching for better accuracy
            if re.search(r'\b' + re.escape(keyword.lower()) + r'\b', normalized_text):
                detected_tags.append({
                    'name': tag_name,
                    'color': pattern_info['color'],
                    'icon': pattern_info['icon']
                })
                break  # Don't add the same tag multiple times
    
    # Remove duplicates and limit to max_tags
    unique_tags = []
    seen = set()
    for tag in detected_tags:
        if tag['name'] not in seen:
            seen.add(tag['name'])
            unique_tags.append(tag)
            if len(unique_tags) >= max_tags:
                break
    
    return unique_tags


def suggest_tags_for_expense(description: str, ocr_text: str = None, category_name: str = None) -> List[Dict[str, str]]:
    """
    Suggest tags for an expense based on description, OCR text, and category
    
    Args:
        description: The expense description
        ocr_text: OCR text from receipt (if available)
        category_name: The category name (if available)
        
    Returns:
        List of suggested tag dictionaries
    """
    all_text = description
    
    # Combine all available text
    if ocr_text:
        all_text += " " + ocr_text
    if category_name:
        all_text += " " + category_name
    
    return extract_tags_from_text(all_text, max_tags=3)


def get_tag_suggestions() -> Dict[str, List[str]]:
    """
    Get all available tag patterns for UI display
    
    Returns:
        Dictionary of tag names to their keywords
    """
    suggestions = {}
    for tag_name, pattern_info in TAG_PATTERNS.items():
        suggestions[tag_name] = {
            'keywords': pattern_info['keywords'][:5],  # Show first 5 keywords
            'color': pattern_info['color'],
            'icon': pattern_info['icon']
        }
    return suggestions
