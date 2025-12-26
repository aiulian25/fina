from PIL import Image, ImageDraw, ImageFont
import os

def create_fina_logo_round(size):
    # Create image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    center = size // 2
    
    # Outer border circle (light blue/cyan ring)
    border_width = int(size * 0.05)
    draw.ellipse([0, 0, size, size], fill=(100, 180, 230, 255))
    draw.ellipse([border_width, border_width, size - border_width, size - border_width], 
                 fill=(0, 0, 0, 0))
    
    # Background circle (dark blue gradient effect)
    for i in range(15):
        radius = (size // 2 - border_width) - i * 2
        alpha = 255
        color = (0, 50 + i * 3, 80 + i * 5, alpha)
        draw.ellipse([center - radius, center - radius, center + radius, center + radius], fill=color)
    
    # White inner circle
    inner_radius = int(size * 0.38)
    draw.ellipse([center - inner_radius, center - inner_radius, center + inner_radius, center + inner_radius], 
                 fill=(245, 245, 245, 255))
    
    # Shield (cyan/turquoise) - smaller for round design
    shield_size = int(size * 0.22)
    shield_x = int(center - shield_size * 0.6)
    shield_y = int(center - shield_size * 0.4)
    
    # Draw shield shape
    shield_points = [
        (shield_x, shield_y),
        (shield_x + shield_size, shield_y),
        (shield_x + shield_size, shield_y + int(shield_size * 0.7)),
        (shield_x + shield_size // 2, shield_y + int(shield_size * 1.2)),
        (shield_x, shield_y + int(shield_size * 0.7))
    ]
    draw.polygon(shield_points, fill=(64, 224, 208, 220))
    
    # Coins (orange/golden) - adjusted position
    coin_radius = int(size * 0.07)
    coin_x = int(center + shield_size * 0.35)
    coin_y = int(center - shield_size * 0.15)
    
    # Draw 3 stacked coins
    for i in range(3):
        y_offset = coin_y + i * int(coin_radius * 0.55)
        # Coin shadow
        draw.ellipse([coin_x - coin_radius + 2, y_offset - coin_radius + 2,
                     coin_x + coin_radius + 2, y_offset + coin_radius + 2],
                    fill=(100, 70, 0, 100))
        # Coin body (gradient effect)
        for j in range(5):
            r = coin_radius - j
            brightness = 255 - j * 20
            draw.ellipse([coin_x - r, y_offset - r, coin_x + r, y_offset + r],
                        fill=(255, 180 - j * 10, 50 - j * 5, 255))
    
    # Text "FINA"
    try:
        font_size = int(size * 0.13)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    text = "FINA"
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_x = center - text_width // 2
    text_y = int(center + inner_radius * 0.45)
    
    # Text with cyan color
    draw.text((text_x, text_y), text, fill=(43, 140, 238, 255), font=font)
    
    return img

# Create all logo sizes
print("Creating round FINA logos...")

# Main logo for web app
logo_512 = create_fina_logo_round(512)
logo_512.save('logo.png')
logo_512.save('icon-512x512.png')
print("✓ Created logo.png (512x512)")

# PWA icon
logo_192 = create_fina_logo_round(192)
logo_192.save('icon-192x192.png')
print("✓ Created icon-192x192.png")

# Favicon
logo_64 = create_fina_logo_round(64)
logo_64.save('favicon.png')
print("✓ Created favicon.png (64x64)")

# Small icon for notifications
logo_96 = create_fina_logo_round(96)
logo_96.save('icon-96x96.png')
print("✓ Created icon-96x96.png")

# Apple touch icon
logo_180 = create_fina_logo_round(180)
logo_180.save('apple-touch-icon.png')
print("✓ Created apple-touch-icon.png (180x180)")

print("\nAll round FINA logos created successfully!")
print("Logos are circular/round shaped for PWA, notifications, and web app use.")
