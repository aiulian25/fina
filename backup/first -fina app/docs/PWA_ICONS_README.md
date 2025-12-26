# PWA Icons Guide

For optimal PWA support, you should add multiple icon sizes. Place these in `app/static/images/`:

## Required Icons:
- `icon-72x72.png` (72x72)
- `icon-96x96.png` (96x96)
- `icon-128x128.png` (128x128)
- `icon-144x144.png` (144x144)
- `icon-152x152.png` (152x152)
- `icon-192x192.png` (192x192)
- `icon-384x384.png` (384x384)
- `icon-512x512.png` (512x512)

## Generate Icons:
You can use your existing `fina-logo.png` and resize it to create these icons.

Using ImageMagick:
```bash
cd app/static/images/
for size in 72 96 128 144 152 192 384 512; do
  convert fina-logo.png -resize ${size}x${size} icon-${size}x${size}.png
done
```

Or use online tools like:
- https://realfavicongenerator.net/
- https://www.pwabuilder.com/imageGenerator

## Update manifest.json
After creating the icons, update the manifest.json icons array with all sizes.
