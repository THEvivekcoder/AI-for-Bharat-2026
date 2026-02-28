# PWA Icons

This directory should contain PWA icons in various sizes.

## Required Sizes

- icon-72x72.png
- icon-96x96.png
- icon-128x128.png
- icon-144x144.png
- icon-152x152.png
- icon-192x192.png
- icon-384x384.png
- icon-512x512.png

## Generating Icons

You can generate icons from a single source image using:

### Online Tools
- [RealFaviconGenerator](https://realfavicongenerator.net/)
- [PWA Builder](https://www.pwabuilder.com/)
- [Favicon.io](https://favicon.io/)

### Command Line (ImageMagick)

```bash
# Install ImageMagick
# Ubuntu/Debian: sudo apt-get install imagemagick
# macOS: brew install imagemagick

# Generate all sizes from source.png
convert source.png -resize 72x72 icon-72x72.png
convert source.png -resize 96x96 icon-96x96.png
convert source.png -resize 128x128 icon-128x128.png
convert source.png -resize 144x144 icon-144x144.png
convert source.png -resize 152x152 icon-152x152.png
convert source.png -resize 192x192 icon-192x192.png
convert source.png -resize 384x384 icon-384x384.png
convert source.png -resize 512x512 icon-512x512.png
```

### Python Script

```python
from PIL import Image
import os

sizes = [72, 96, 128, 144, 152, 192, 384, 512]
source = "source.png"

img = Image.open(source)

for size in sizes:
    resized = img.resize((size, size), Image.LANCZOS)
    resized.save(f"icon-{size}x{size}.png")
    print(f"Generated icon-{size}x{size}.png")
```

## Design Guidelines

- Use a simple, recognizable design
- Ensure good contrast for visibility
- Test on both light and dark backgrounds
- Consider maskable icon requirements
- Use PNG format with transparency

## Maskable Icons

For better Android support, create maskable icons with:
- Safe zone: 80% of canvas (40% radius circle)
- Padding: 10% on all sides
- Background: Solid color or gradient

## Current Status

⚠️ **Placeholder icons needed** - Generate icons before production deployment.

For development, you can use a simple colored square or the BharatSahayak logo.
