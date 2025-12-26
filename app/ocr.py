"""
OCR Processing Utility
Extracts text from images and PDFs for searchability
Security: All file paths validated before processing
"""
import os
import tempfile
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import cv2
import numpy as np


def preprocess_image(image):
    """
    Preprocess image to improve OCR accuracy
    - Convert to grayscale
    - Apply adaptive thresholding
    - Denoise
    """
    try:
        # Convert PIL Image to numpy array
        img_array = np.array(image)
        
        # Convert to grayscale
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
        
        # Convert back to PIL Image
        return Image.fromarray(denoised)
    except Exception as e:
        print(f"Error preprocessing image: {str(e)}")
        # Return original image if preprocessing fails
        return image


def extract_text_from_image(image_path):
    """
    Extract text from an image file using OCR
    Supports: PNG, JPG, JPEG
    Security: Validates file exists and is readable
    Returns: Extracted text or empty string on failure
    """
    try:
        # Security: Validate file exists
        if not os.path.exists(image_path):
            print(f"Image file not found: {image_path}")
            return ""
        
        # Open and preprocess image
        image = Image.open(image_path)
        preprocessed = preprocess_image(image)
        
        # Extract text using Tesseract with English + Romanian
        text = pytesseract.image_to_string(
            preprocessed,
            lang='eng+ron',  # Support both English and Romanian
            config='--psm 6'  # Assume uniform block of text
        )
        
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from image {image_path}: {str(e)}")
        return ""


def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file using OCR
    Converts PDF pages to images, then applies OCR
    Security: Validates file exists and is readable
    Returns: Extracted text or empty string on failure
    """
    try:
        # Security: Validate file exists
        if not os.path.exists(pdf_path):
            print(f"PDF file not found: {pdf_path}")
            return ""
        
        # Convert PDF to images (first 10 pages max to avoid memory issues)
        pages = convert_from_path(pdf_path, first_page=1, last_page=10, dpi=300)
        
        extracted_text = []
        for i, page in enumerate(pages):
            # Preprocess page
            preprocessed = preprocess_image(page)
            
            # Extract text
            text = pytesseract.image_to_string(
                preprocessed,
                lang='eng+ron',
                config='--psm 6'
            )
            
            if text.strip():
                extracted_text.append(f"--- Page {i+1} ---\n{text.strip()}")
        
        return "\n\n".join(extracted_text)
    except Exception as e:
        print(f"Error extracting text from PDF {pdf_path}: {str(e)}")
        return ""


def extract_text_from_file(file_path, file_type):
    """
    Extract text from any supported file type
    Security: Validates file path and type before processing
    
    Args:
        file_path: Absolute path to the file
        file_type: File extension (pdf, png, jpg, jpeg)
    
    Returns:
        Extracted text or empty string on failure
    """
    try:
        # Security: Validate file path
        if not os.path.isabs(file_path):
            print(f"Invalid file path (not absolute): {file_path}")
            return ""
        
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return ""
        
        # Normalize file type
        file_type = file_type.lower().strip('.')
        
        # Route to appropriate extractor
        if file_type == 'pdf':
            return extract_text_from_pdf(file_path)
        elif file_type in ['png', 'jpg', 'jpeg']:
            return extract_text_from_image(file_path)
        else:
            print(f"Unsupported file type for OCR: {file_type}")
            return ""
    except Exception as e:
        print(f"Error in extract_text_from_file: {str(e)}")
        return ""


def process_ocr_async(file_path, file_type):
    """
    Wrapper for async OCR processing
    Can be used with background jobs if needed
    
    Returns:
        Dictionary with success status and extracted text
    """
    try:
        text = extract_text_from_file(file_path, file_type)
        return {
            'success': True,
            'text': text,
            'length': len(text)
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'text': ''
        }
