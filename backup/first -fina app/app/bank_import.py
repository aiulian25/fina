"""
Bank Statement Import Module for FINA Finance Tracker
Parses PDF and CSV bank statements and extracts transactions
"""
import re
import csv
import io
from datetime import datetime
from decimal import Decimal
import PyPDF2


class BankStatementParser:
    """Base parser class for bank statements"""
    
    def __init__(self):
        self.transactions = []
        self.detected_format = None
        self.total_transactions = 0
        self.parse_errors = []
    
    def parse(self, file_content, file_type):
        """
        Main parse method - detects format and extracts transactions
        
        Args:
            file_content: File content (bytes for PDF, string for CSV)
            file_type: 'pdf' or 'csv'
        
        Returns:
            dict with transactions and metadata
        """
        if file_type == 'pdf':
            return self.parse_pdf(file_content)
        elif file_type == 'csv':
            return self.parse_csv(file_content)
        else:
            return {'success': False, 'error': 'Unsupported file type'}
    
    def parse_pdf(self, pdf_bytes):
        """
        Parse PDF bank statement
        Extracts transactions using pattern matching
        """
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            text = ""
            
            # Extract text from all pages
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            # Detect bank format
            bank_format = self.detect_bank_format(text)
            
            # Parse transactions based on detected format
            if bank_format == 'generic':
                transactions = self.parse_generic_pdf(text)
            else:
                transactions = self.parse_generic_pdf(text)  # Fallback to generic
            
            return {
                'success': True,
                'transactions': transactions,
                'total_found': len(transactions),
                'bank_format': bank_format,
                'parse_errors': self.parse_errors
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'PDF parsing failed: {str(e)}',
                'transactions': []
            }
    
    def parse_csv(self, csv_string):
        """
        Parse CSV bank statement
        Auto-detects column mapping
        """
        try:
            # Try different delimiters
            delimiter = self.detect_csv_delimiter(csv_string)
            
            stream = io.StringIO(csv_string)
            csv_reader = csv.DictReader(stream, delimiter=delimiter)
            
            # Auto-detect column names
            fieldnames = csv_reader.fieldnames
            column_map = self.detect_csv_columns(fieldnames)
            
            transactions = []
            row_num = 0
            
            for row in csv_reader:
                row_num += 1
                try:
                    transaction = self.extract_transaction_from_csv_row(row, column_map)
                    if transaction:
                        transactions.append(transaction)
                except Exception as e:
                    self.parse_errors.append(f"Row {row_num}: {str(e)}")
            
            return {
                'success': True,
                'transactions': transactions,
                'total_found': len(transactions),
                'column_mapping': column_map,
                'parse_errors': self.parse_errors
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'CSV parsing failed: {str(e)}',
                'transactions': []
            }
    
    def detect_bank_format(self, text):
        """Detect which bank format the PDF uses"""
        text_lower = text.lower()
        
        # Add patterns for specific banks
        if 'revolut' in text_lower:
            return 'revolut'
        elif 'ing' in text_lower or 'ing bank' in text_lower:
            return 'ing'
        elif 'bcr' in text_lower or 'banca comercială' in text_lower:
            return 'bcr'
        elif 'brd' in text_lower:
            return 'brd'
        else:
            return 'generic'
    
    def parse_generic_pdf(self, text):
        """
        Parse PDF using generic patterns
        Looks for common transaction patterns across banks
        """
        transactions = []
        lines = text.split('\n')
        
        # Common patterns for transactions
        # Date patterns: DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD
        date_patterns = [
            r'(\d{2}[/-]\d{2}[/-]\d{4})',  # DD/MM/YYYY or DD-MM-YYYY
            r'(\d{4}[/-]\d{2}[/-]\d{2})',  # YYYY-MM-DD
        ]
        
        # Amount patterns: -123.45, 123.45, 123,45, -123,45
        amount_patterns = [
            r'[-]?\d{1,10}[.,]\d{2}',  # With 2 decimals
            r'[-]?\d{1,10}\s*(?:RON|EUR|USD|GBP|LEI)',  # With currency
        ]
        
        for i, line in enumerate(lines):
            # Skip header lines
            if any(word in line.lower() for word in ['sold', 'balance', 'iban', 'account', 'statement']):
                continue
            
            # Look for date in line
            date_match = None
            for pattern in date_patterns:
                match = re.search(pattern, line)
                if match:
                    date_match = match.group(1)
                    break
            
            if not date_match:
                continue
            
            # Parse date
            trans_date = self.parse_date(date_match)
            if not trans_date:
                continue
            
            # Look for amount in this line and nearby lines
            amount = None
            description = line
            
            # Check current line and next 2 lines for amount
            for j in range(i, min(i + 3, len(lines))):
                amounts_found = re.findall(r'[-]?\d{1,10}[.,]\d{2}', lines[j])
                if amounts_found:
                    # Take the last amount (usually the transaction amount)
                    amount_str = amounts_found[-1]
                    amount = self.parse_amount(amount_str)
                    break
            
            if not amount or amount == 0:
                continue
            
            # Clean description
            description = self.clean_description(line, date_match, str(amount))
            
            if description:
                transactions.append({
                    'date': trans_date,
                    'description': description,
                    'amount': abs(amount),  # Always positive, type determined by sign
                    'type': 'expense' if amount < 0 else 'income',
                    'original_amount': amount
                })
        
        # Deduplicate based on date + amount + description similarity
        transactions = self.deduplicate_transactions(transactions)
        
        return transactions
    
    def detect_csv_delimiter(self, csv_string):
        """Detect CSV delimiter (comma, semicolon, tab)"""
        first_line = csv_string.split('\n')[0]
        
        comma_count = first_line.count(',')
        semicolon_count = first_line.count(';')
        tab_count = first_line.count('\t')
        
        if semicolon_count > comma_count and semicolon_count > tab_count:
            return ';'
        elif tab_count > comma_count:
            return '\t'
        else:
            return ','
    
    def detect_csv_columns(self, fieldnames):
        """
        Auto-detect which columns contain date, description, amount
        Returns mapping of column indices
        """
        fieldnames_lower = [f.lower() if f else '' for f in fieldnames]
        
        column_map = {
            'date': None,
            'description': None,
            'amount': None,
            'debit': None,
            'credit': None
        }
        
        # Date column keywords
        date_keywords = ['date', 'data', 'fecha', 'datum', 'transaction date']
        for idx, name in enumerate(fieldnames_lower):
            if any(keyword in name for keyword in date_keywords):
                column_map['date'] = fieldnames[idx]
                break
        
        # Description column keywords
        desc_keywords = ['description', 'descriere', 'descripción', 'details', 'detalii', 'merchant', 'comerciant']
        for idx, name in enumerate(fieldnames_lower):
            if any(keyword in name for keyword in desc_keywords):
                column_map['description'] = fieldnames[idx]
                break
        
        # Amount columns
        amount_keywords = ['amount', 'suma', 'monto', 'valoare']
        debit_keywords = ['debit', 'withdrawal', 'retragere', 'retiro', 'spent']
        credit_keywords = ['credit', 'deposit', 'depunere', 'ingreso', 'income']
        
        for idx, name in enumerate(fieldnames_lower):
            if any(keyword in name for keyword in amount_keywords):
                column_map['amount'] = fieldnames[idx]
            elif any(keyword in name for keyword in debit_keywords):
                column_map['debit'] = fieldnames[idx]
            elif any(keyword in name for keyword in credit_keywords):
                column_map['credit'] = fieldnames[idx]
        
        return column_map
    
    def extract_transaction_from_csv_row(self, row, column_map):
        """Extract transaction data from CSV row using column mapping"""
        # Get date
        date_col = column_map.get('date')
        if not date_col or date_col not in row:
            return None
        
        trans_date = self.parse_date(row[date_col])
        if not trans_date:
            return None
        
        # Get description
        desc_col = column_map.get('description')
        description = row.get(desc_col, 'Transaction') if desc_col else 'Transaction'
        
        # Get amount
        amount = 0
        trans_type = 'expense'
        
        # Check if we have separate debit/credit columns
        if column_map.get('debit') and column_map.get('credit'):
            debit_val = self.parse_amount(row.get(column_map['debit'], '0'))
            credit_val = self.parse_amount(row.get(column_map['credit'], '0'))
            
            if debit_val > 0:
                amount = debit_val
                trans_type = 'expense'
            elif credit_val > 0:
                amount = credit_val
                trans_type = 'income'
        elif column_map.get('amount'):
            amount_val = self.parse_amount(row.get(column_map['amount'], '0'))
            amount = abs(amount_val)
            trans_type = 'expense' if amount_val < 0 else 'income'
        
        if amount == 0:
            return None
        
        return {
            'date': trans_date,
            'description': description.strip(),
            'amount': amount,
            'type': trans_type
        }
    
    def parse_date(self, date_str):
        """Parse date string in various formats"""
        date_str = date_str.strip()
        
        # Try different date formats
        formats = [
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%d.%m.%Y',
            '%m/%d/%Y',
            '%d %b %Y',
            '%d %B %Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        return None
    
    def parse_amount(self, amount_str):
        """Parse amount string to float"""
        if not amount_str:
            return 0.0
        
        # Remove currency symbols and whitespace
        amount_str = str(amount_str).strip()
        amount_str = re.sub(r'[^\d.,-]', '', amount_str)
        
        if not amount_str:
            return 0.0
        
        # Handle comma as decimal separator (European format)
        if ',' in amount_str and '.' in amount_str:
            # Format: 1.234,56 -> remove dots, replace comma with dot
            amount_str = amount_str.replace('.', '').replace(',', '.')
        elif ',' in amount_str:
            # Format: 1234,56 -> replace comma with dot
            amount_str = amount_str.replace(',', '.')
        
        try:
            return float(amount_str)
        except ValueError:
            return 0.0
    
    def clean_description(self, text, date_str, amount_str):
        """Clean transaction description by removing date and amount"""
        # Remove date
        text = text.replace(date_str, '')
        # Remove amount
        text = text.replace(amount_str, '')
        # Remove extra whitespace
        text = ' '.join(text.split())
        # Remove common keywords
        remove_words = ['transaction', 'payment', 'transfer', 'tranzactie', 'plata']
        for word in remove_words:
            text = re.sub(word, '', text, flags=re.IGNORECASE)
        
        text = text.strip()
        
        # If too short, return generic
        if len(text) < 3:
            return 'Bank Transaction'
        
        return text[:200]  # Limit length
    
    def deduplicate_transactions(self, transactions):
        """Remove duplicate transactions"""
        seen = set()
        unique = []
        
        for trans in transactions:
            # Create signature: date + amount + first 20 chars of description
            signature = (
                trans['date'].isoformat(),
                round(trans['amount'], 2),
                trans['description'][:20].lower()
            )
            
            if signature not in seen:
                seen.add(signature)
                unique.append(trans)
        
        return unique
    
    def validate_file(self, file_content, file_type, max_size_mb=10):
        """
        Validate uploaded file
        
        Args:
            file_content: File content bytes
            file_type: 'pdf' or 'csv'
            max_size_mb: Maximum file size in MB
        
        Returns:
            (is_valid, error_message)
        """
        # Check file size
        size_mb = len(file_content) / (1024 * 1024)
        if size_mb > max_size_mb:
            return False, f'File too large. Maximum size is {max_size_mb}MB'
        
        # Check file type
        if file_type == 'pdf':
            # Check PDF header
            if not file_content.startswith(b'%PDF'):
                return False, 'Invalid PDF file'
        elif file_type == 'csv':
            # Try to decode as text
            try:
                file_content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    file_content.decode('latin-1')
                except:
                    return False, 'Invalid CSV file encoding'
        else:
            return False, 'Unsupported file type. Use PDF or CSV'
        
        return True, None


def parse_bank_statement(file_content, filename):
    """
    Main entry point for bank statement parsing
    
    Args:
        file_content: File content as bytes
        filename: Original filename
    
    Returns:
        Parse results dictionary
    """
    parser = BankStatementParser()
    
    # Determine file type
    file_ext = filename.lower().split('.')[-1]
    if file_ext == 'pdf':
        file_type = 'pdf'
        content = file_content
    elif file_ext == 'csv':
        file_type = 'csv'
        # Try to decode
        try:
            content = file_content.decode('utf-8')
        except UnicodeDecodeError:
            content = file_content.decode('latin-1', errors='ignore')
    else:
        return {
            'success': False,
            'error': 'Unsupported file type. Please upload PDF or CSV files.'
        }
    
    # Validate file
    is_valid, error_msg = parser.validate_file(file_content, file_type)
    if not is_valid:
        return {'success': False, 'error': error_msg}
    
    # Parse file
    result = parser.parse(content, file_type)
    
    return result
