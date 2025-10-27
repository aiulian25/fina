def get_currency_symbol(currency_code):
    """Get currency symbol for display"""
    symbols = {
        'USD': '$',
        'EUR': '€',
        'RON': 'Lei',
        'GBP': '£'
    }
    return symbols.get(currency_code, '$')

def format_currency(amount, currency_code='USD'):
    """Format amount with currency symbol"""
    symbol = get_currency_symbol(currency_code)
    
    # Format number with 2 decimals
    formatted_amount = f"{amount:,.2f}"
    
    # Position symbol based on currency
    if currency_code == 'RON':
        return f"{formatted_amount} {symbol}"  # Romanian Leu after amount
    else:
        return f"{symbol}{formatted_amount}"  # Symbol before amount
