from PIL import Image, ImageDraw, ImageFont
import os

def create_fina_logo(size):
    # Create image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Background circle (dark blue gradient effect)
    center = size // 2
    for i in range(10):
        radius = size // 2 - i * 2
        alpha = 255 - i * 20
        color = (0, 50 + i * 5, 80 + i * 8, alpha)
        draw.ellipse([center - radius, center - radius, center + radius, center + radius], fill=color)
    
    # White inner circle
    inner_radius = int(size * 0.42)
    draw.ellipse([center - inner_radius, center - inner_radius, center + inner_radius, center + inner_radius], 
                 fill=(245, 245, 245, 255))
    
    # Shield (cyan/turquoise)
    shield_size = int(size * 0.25)
    shield_x = int(center - shield_size * 0.5)
    shield_y = int(center - shield_size * 0.3)
    
    # Draw shield shape
    shield_points = [
        (shield_x, shield_y),
        (shield_x + shield_size, shield_y),
        (shield_x + shield_size, shield_y + int(shield_size * 0.7)),
        (shield_x + shield_size // 2, shield_y + int(shield_size * 1.2)),
        (shield_x, shield_y + int(shield_size * 0.7))
    ]
    draw.polygon(shield_points, fill=(64, 224, 208, 200))
    
    # Coins (orange/golden)
    coin_radius = int(size * 0.08)
    coin_x = int(center + shield_size * 0.3)
    coin_y = int(center - shield_size * 0.1)
    
    # Draw 3 stacked coins
    for i in range(3):
        y_offset = coin_y + i * int(coin_radius * 0.6)
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
        # Try to use a bold font
        font_size = int(size * 0.15)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    text = "FINA"
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_x = center - text_width // 2
    text_y = int(center + inner_radius * 0.5)
    
    # Text with cyan color
    draw.text((text_x, text_y), text, fill=(64, 200, 224, 255), font=font)
    
    return img

# Create logos
logo_512 = create_fina_logo(512)
logo_512.save('logo.png')
logo_512.save('icon-512x512.png')

logo_192 = create_fina_logo(192)
logo_192.save('icon-192x192.png')

logo_64 = create_fina_logo(64)
logo_64.save('favicon.png')

print("FINA logos created successfully!")
