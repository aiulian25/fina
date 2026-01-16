#!/usr/bin/env python3
"""
Generate PWA screenshots for manifest.json
Creates placeholder screenshots with FINA branding
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_screenshot(width, height, filename, is_wide=False):
    """Create a branded screenshot placeholder"""
    
    # Dark background matching app theme
    img = Image.new('RGB', (width, height), (17, 26, 34))  # #111a22
    draw = ImageDraw.Draw(img)
    
    # Add gradient header area
    header_height = int(height * 0.12)
    for y in range(header_height):
        alpha = 1 - (y / header_height) * 0.5
        r = int(43 * alpha)
        g = int(140 * alpha)
        b = int(238 * alpha)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # Try to load font
    try:
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]
        font_large = None
        font_small = None
        for path in font_paths:
            if os.path.exists(path):
                font_large = ImageFont.truetype(path, int(height * 0.06))
                font_small = ImageFont.truetype(path, int(height * 0.03))
                break
        if not font_large:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Draw "FINA" title in header
    title = "FINA"
    bbox = draw.textbbox((0, 0), title, font=font_large)
    text_width = bbox[2] - bbox[0]
    draw.text((int(width * 0.05), int(header_height * 0.3)), title, fill=(255, 255, 255), font=font_large)
    
    # Draw card-like elements to simulate dashboard
    card_margin = int(width * 0.04)
    card_width = (width - card_margin * 3) // 2 if is_wide else width - card_margin * 2
    card_height = int(height * 0.15)
    card_y = header_height + int(height * 0.05)
    card_radius = 12
    
    # Draw 4 cards (2x2 grid for wide, 2x2 for narrow)
    cards = [
        ("Total Income", "£2,450.00", (46, 204, 113)),    # Green
        ("Expenses", "£1,234.56", (231, 76, 60)),         # Red
        ("Balance", "£1,215.44", (43, 140, 238)),         # Blue
        ("Savings", "£500.00", (155, 89, 182)),           # Purple
    ]
    
    if is_wide:
        # 4 cards in a row for wide screenshot
        card_width = (width - card_margin * 5) // 4
        for i, (label, value, color) in enumerate(cards):
            x = card_margin + i * (card_width + card_margin)
            draw.rounded_rectangle(
                [x, card_y, x + card_width, card_y + card_height],
                radius=card_radius,
                fill=(35, 54, 72)  # #233648
            )
            # Label
            draw.text((x + 15, card_y + 15), label, fill=(146, 173, 201), font=font_small)
            # Value
            draw.text((x + 15, card_y + card_height - 45), value, fill=color, font=font_large)
    else:
        # 2x2 grid for narrow screenshot
        for i, (label, value, color) in enumerate(cards):
            col = i % 2
            row = i // 2
            x = card_margin + col * (card_width + card_margin)
            y = card_y + row * (card_height + card_margin)
            draw.rounded_rectangle(
                [x, y, x + card_width, y + card_height],
                radius=card_radius,
                fill=(35, 54, 72)
            )
            draw.text((x + 15, y + 15), label, fill=(146, 173, 201), font=font_small)
            draw.text((x + 15, y + card_height - 45), value, fill=color, font=font_large)
    
    # Draw chart area
    chart_y = card_y + (card_height + card_margin) * (1 if is_wide else 2) + card_margin
    chart_height = int(height * 0.25)
    draw.rounded_rectangle(
        [card_margin, chart_y, width - card_margin, chart_y + chart_height],
        radius=card_radius,
        fill=(35, 54, 72)
    )
    draw.text((card_margin + 15, chart_y + 15), "Monthly Spending", fill=(255, 255, 255), font=font_small)
    
    # Draw simple bar chart
    bar_count = 7 if is_wide else 5
    bar_width = (width - card_margin * 4) // (bar_count * 2)
    bar_max_height = chart_height - 80
    bar_y_base = chart_y + chart_height - 30
    bar_heights = [0.6, 0.8, 0.5, 0.9, 0.7, 0.4, 0.75][:bar_count]
    
    for i, h in enumerate(bar_heights):
        bar_x = card_margin * 2 + i * bar_width * 2
        bar_h = int(bar_max_height * h)
        draw.rounded_rectangle(
            [bar_x, bar_y_base - bar_h, bar_x + bar_width, bar_y_base],
            radius=4,
            fill=(43, 140, 238)
        )
    
    # Draw bottom navigation for mobile
    if not is_wide:
        nav_height = int(height * 0.08)
        nav_y = height - nav_height
        draw.rectangle([0, nav_y, width, height], fill=(35, 54, 72))
        
        # Nav icons (simple circles)
        nav_items = 5
        nav_spacing = width // nav_items
        for i in range(nav_items):
            cx = nav_spacing // 2 + i * nav_spacing
            cy = nav_y + nav_height // 2
            radius = 12
            color = (43, 140, 238) if i == 0 else (146, 173, 201)
            draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=color)
    
    return img


if __name__ == "__main__":
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'screenshots')
    os.makedirs(output_dir, exist_ok=True)
    
    print("Generating PWA screenshots...")
    
    # Mobile screenshot (narrow) - required for mobile install
    mobile = create_screenshot(540, 1170, 'screenshot-mobile.png', is_wide=False)
    mobile.save(os.path.join(output_dir, 'screenshot-mobile.png'), 'PNG')
    print("  ✓ Created screenshot-mobile.png (540x1170)")
    
    # Desktop screenshot (wide) - required for desktop install
    desktop = create_screenshot(1280, 720, 'screenshot-desktop.png', is_wide=True)
    desktop.save(os.path.join(output_dir, 'screenshot-desktop.png'), 'PNG')
    print("  ✓ Created screenshot-desktop.png (1280x720)")
    
    print("\n✅ Screenshots generated successfully!")
