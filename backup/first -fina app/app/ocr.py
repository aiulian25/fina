"""
Receipt OCR Module
Extracts amount, date, and merchant information from receipt images using Tesseract OCR
"""

import pytesseract
from PIL import Image
import re
from datetime import datetime
from dateutil import parser as date_parser
import os


def extract_receipt_data(image_path):
    """
    Extract structured data from receipt image
    
    Args:
        image_path: Path to the receipt image file
    
    Returns:
        dict with extracted data: {
            'amount': float or None,
            'date': datetime or None,
            'merchant': str or None,
            'raw_text': str,
            'confidence': str ('high', 'medium', 'low')
        }
    """
    try:
        # Open and preprocess image
        image = Image.open(image_path)
        
        # Convert to grayscale for better OCR
        if image.mode != 'L':
            image = image.convert('L')
        
        # Perform OCR
        text = pytesseract.image_to_string(image, config='--psm 6')
        
        # Extract structured data
        amount = extract_amount(text)
        date = extract_date(text)
        merchant = extract_merchant(text)
        
        # Determine confidence level
        confidence = calculate_confidence(amount, date, merchant, text)
        
        return {
            'amount': amount,
            'date': date,
            'merchant': merchant,
            'raw_text': text,
            'confidence': confidence,
            'success': True
        }
        
    except Exception as e:
        return {
            'amount': None,
            'date': None,
            'merchant': None,
            'raw_text': '',
            'confidence': 'none',
            'success': False,
            'error': str(e)
        }


def extract_amount(text):
    """
    Extract monetary amount from text
    Supports multiple formats: $10.99, 10.99, 10,99, etc.
    """
    # Common patterns for amounts
    patterns = [
        r'(?:total|suma|amount|subtotal|plata)[\s:]*[\$€£]?\s*(\d{1,6}[.,]\d{2})',  # Total: $10.99
        r'[\$€£]\s*(\d{1,6}[.,]\d{2})',  # $10.99
        r'(\d{1,6}[.,]\d{2})\s*(?:RON|USD|EUR|GBP|lei)',  # 10.99 RON
        r'(?:^|\s)(\d{1,6}[.,]\d{2})(?:\s|$)',  # Standalone 10.99
    ]
    
    amounts = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            # Normalize comma to dot
            amount_str = match.replace(',', '.')
            try:
                amount = float(amount_str)
                if 0.01 <= amount <= 999999:  # Reasonable range
                    amounts.append(amount)
            except ValueError:
                continue
    
    if amounts:
        # Return the largest amount (usually the total)
        return max(amounts)
    
    return None


def extract_date(text):
    """
    Extract date from text
    Supports multiple formats: DD/MM/YYYY, MM-DD-YYYY, DD.MM.YYYY, etc.
    """
    # Common date patterns
    date_patterns = [
        r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # DD/MM/YYYY, MM-DD-YYYY
        r'\d{1,2}\.\d{1,2}\.\d{2,4}',  # DD.MM.YYYY
        r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',  # YYYY-MM-DD
        r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}',  # Jan 15, 2024
        r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}',  # 15 Jan 2024
    ]
    
    dates = []
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                # Try to parse the date
                parsed_date = date_parser.parse(match, fuzzy=True)
                
                # Only accept dates within reasonable range
                if datetime(2000, 1, 1) <= parsed_date <= datetime.now():
                    dates.append(parsed_date)
            except (ValueError, date_parser.ParserError):
                continue
    
    if dates:
        # Return the most recent date (likely the transaction date)
        return max(dates)
    
    return None


def extract_merchant(text):
    """
    Extract merchant/store name from text
    Usually appears at the top of the receipt
    """
    lines = text.strip().split('\n')
    
    # Look at first few lines for merchant name
    for i, line in enumerate(lines[:5]):
        line = line.strip()
        
        # Skip very short lines
        if len(line) < 3:
            continue
        
        # Skip lines that look like addresses or numbers
        if re.match(r'^[\d\s\.,]+$', line):
            continue
        
        # Skip common keywords
        if re.match(r'^(receipt|factura|bon|total|date|time)', line, re.IGNORECASE):
            continue
        
        # If line has letters and reasonable length, likely merchant
        if re.search(r'[a-zA-Z]{3,}', line) and 3 <= len(line) <= 50:
            # Clean up the line
            cleaned = re.sub(r'[^\w\s-]', ' ', line)
            cleaned = ' '.join(cleaned.split())
            
            if cleaned:
                return cleaned
    
    return None


def calculate_confidence(amount, date, merchant, text):
    """
    Calculate confidence level of extraction
    
    Returns: 'high', 'medium', 'low', or 'none'
    """
    found_count = sum([
        amount is not None,
        date is not None,
        merchant is not None
    ])
    
    # Check text quality
    text_quality = len(text.strip()) > 50 and len(text.split()) > 10
    
    if found_count == 3 and text_quality:
        return 'high'
    elif found_count >= 2:
        return 'medium'
    elif found_count >= 1:
        return 'low'
    else:
        return 'none'


def preprocess_image_for_ocr(image_path, output_path=None):
    """
    Preprocess image to improve OCR accuracy
    
    Args:
        image_path: Path to original image
        output_path: Path to save preprocessed image (optional)
    
    Returns:
        PIL Image object
    """
    from PIL import ImageEnhance, ImageFilter
    
    image = Image.open(image_path)
    
    # Convert to grayscale
    image = image.convert('L')
    
    # Increase contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)
    
    # Sharpen image
    image = image.filter(ImageFilter.SHARPEN)
    
    # Apply threshold (binarization)
    threshold = 128
    image = image.point(lambda p: 255 if p > threshold else 0)
    
    if output_path:
        image.save(output_path)
    
    return image


def is_valid_receipt_image(image_path):
    """
    Validate that uploaded file is a valid image
    
    Security check to prevent malicious files
    """
    try:
        image = Image.open(image_path)
        image.verify()
        
        # Check file size (max 10MB)
        file_size = os.path.getsize(image_path)
        if file_size > 10 * 1024 * 1024:
            return False, "File too large (max 10MB)"
        
        # Check image dimensions (reasonable receipt size)
        image = Image.open(image_path)
        width, height = image.size
        if width < 100 or height < 100:
            return False, "Image too small"
        if width > 8000 or height > 8000:
            return False, "Image too large"
        
        # Check format
        if image.format not in ['JPEG', 'PNG', 'JPG']:
            return False, "Unsupported format (use JPEG or PNG)"
        
        return True, "Valid"
        
    except Exception as e:
        return False, f"Invalid image: {str(e)}"


def extract_receipt_data_batch(image_paths):
    """
    Process multiple receipt images in batch
    
    Args:
        image_paths: List of image file paths
    
    Returns:
        List of extraction results
    """
    results = []
    for path in image_paths:
        result = extract_receipt_data(path)
        result['file_path'] = path
        results.append(result)
    return results


def format_extraction_summary(data):
    """
    Format extracted data for display
    
    Returns: Human-readable string
    """
    lines = []
    
    if data.get('merchant'):
        lines.append(f"🏪 Merchant: {data['merchant']}")
    
    if data.get('amount'):
        lines.append(f"💰 Amount: {data['amount']:.2f}")
    
    if data.get('date'):
        lines.append(f"📅 Date: {data['date'].strftime('%Y-%m-%d')}")
    
    if data.get('confidence'):
        confidence_emoji = {
            'high': '✅',
            'medium': '⚠️',
            'low': '❌',
            'none': '❌'
        }
        emoji = confidence_emoji.get(data['confidence'], '❓')
        lines.append(f"{emoji} Confidence: {data['confidence'].title()}")
    
    return '\n'.join(lines) if lines else "No data extracted"
