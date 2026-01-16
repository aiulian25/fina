#!/usr/bin/env python3
"""
Generate professional FINA app icons for PWA and home screen
Run: python generate_icons.py
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_fina_icon(size, with_padding=False):
    """Create a modern, professional FINA finance app icon"""
    
    # Padding for maskable icons (safe zone is 80% of icon)
    if with_padding:
        canvas_size = size
        icon_size = int(size * 0.8)
        offset = (size - icon_size) // 2
    else:
        canvas_size = size
        icon_size = size
        offset = 0
    
    # Create canvas with background color (for maskable icons)
    img = Image.new('RGBA', (canvas_size, canvas_size), (17, 26, 34, 255))  # #111a22
    draw = ImageDraw.Draw(img)
    
    center = canvas_size // 2
    
    # Main circle background - gradient effect with primary blue
    for i in range(15):
        radius = int(icon_size * 0.45) - i * 2
        if radius <= 0:
            break
        # Gradient from #2b8cee to darker blue
        r = max(0, 43 - i * 2)
        g = max(0, 140 - i * 3)
        b = max(0, 238 - i * 5)
        draw.ellipse([
            center - radius, center - radius,
            center + radius, center + radius
        ], fill=(r, g, b, 255))
    
    # Inner white/light circle
    inner_radius = int(icon_size * 0.32)
    draw.ellipse([
        center - inner_radius, center - inner_radius,
        center + inner_radius, center + inner_radius
    ], fill=(255, 255, 255, 255))
    
    # Draw "$" symbol - clean and professional
    try:
        # Try system fonts
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
        ]
        font = None
        font_size = int(icon_size * 0.35)
        for path in font_paths:
            if os.path.exists(path):
                font = ImageFont.truetype(path, font_size)
                break
        if not font:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    # Draw the dollar sign in primary blue
    text = "$"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = center - text_width // 2
    text_y = center - text_height // 2 - int(icon_size * 0.02)  # Slight adjustment for visual center
    
    # Dollar sign in primary blue color
    draw.text((text_x, text_y), text, fill=(43, 140, 238, 255), font=font)  # #2b8cee
    
    # Add subtle shine/highlight on the circle
    shine_radius = int(icon_size * 0.28)
    for i in range(5):
        alpha = 30 - i * 6
        if alpha <= 0:
            break
        r = shine_radius - i * 3
        draw.arc([
            center - r - int(icon_size * 0.05), 
            center - r - int(icon_size * 0.08),
            center + r - int(icon_size * 0.05), 
            center + r - int(icon_size * 0.08)
        ], start=200, end=340, fill=(255, 255, 255, alpha), width=2)
    
    return img


def create_apple_touch_icon(size):
    """Create Apple touch icon with proper rounded corners handled by iOS"""
    return create_fina_icon(size, with_padding=False)


def create_maskable_icon(size):
    """Create maskable icon with safe zone padding"""
    return create_fina_icon(size, with_padding=True)


def create_favicon(size):
    """Create a simple, clear favicon"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    center = size // 2
    radius = int(size * 0.45)
    
    # Blue circle
    draw.ellipse([
        center - radius, center - radius,
        center + radius, center + radius
    ], fill=(43, 140, 238, 255))
    
    # White inner circle
    inner_radius = int(size * 0.32)
    draw.ellipse([
        center - inner_radius, center - inner_radius,
        center + inner_radius, center + inner_radius
    ], fill=(255, 255, 255, 255))
    
    # Simple $ symbol
    try:
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]
        font = None
        font_size = int(size * 0.4)
        for path in font_paths:
            if os.path.exists(path):
                font = ImageFont.truetype(path, font_size)
                break
        if not font:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    text = "$"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = center - text_width // 2
    text_y = center - text_height // 2
    draw.text((text_x, text_y), text, fill=(43, 140, 238, 255), font=font)
    
    return img


if __name__ == "__main__":
    output_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("Generating FINA app icons...")
    
    # Standard icons (any purpose)
    sizes = {
        'icon-512x512.png': (512, False),
        'icon-192x192.png': (192, False),
        'icon-96x96.png': (96, False),
        'logo.png': (512, False),
    }
    
    for filename, (size, maskable) in sizes.items():
        icon = create_fina_icon(size, with_padding=maskable)
        path = os.path.join(output_dir, filename)
        icon.save(path, 'PNG')
        print(f"  ✓ Created {filename}")
    
    # Apple touch icon
    apple_icon = create_apple_touch_icon(180)
    apple_icon.save(os.path.join(output_dir, 'apple-touch-icon.png'), 'PNG')
    print("  ✓ Created apple-touch-icon.png")
    
    # Favicon
    favicon = create_favicon(64)
    favicon.save(os.path.join(output_dir, 'favicon.png'), 'PNG')
    print("  ✓ Created favicon.png")
    
    # Maskable icons (for Android adaptive icons)
    maskable_512 = create_maskable_icon(512)
    maskable_512.save(os.path.join(output_dir, 'icon-512x512-maskable.png'), 'PNG')
    print("  ✓ Created icon-512x512-maskable.png")
    
    maskable_192 = create_maskable_icon(192)
    maskable_192.save(os.path.join(output_dir, 'icon-192x192-maskable.png'), 'PNG')
    print("  ✓ Created icon-192x192-maskable.png")
    
    print("\n✅ All icons generated successfully!")
    print("\nNote: Update manifest.json to use separate maskable icons:")
    print('  - icon-192x192-maskable.png with purpose: "maskable"')
    print('  - icon-512x512-maskable.png with purpose: "maskable"')
