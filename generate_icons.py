#!/usr/bin/env python3
"""Generate PWA icons from logo"""

from PIL import Image
import os

# Source logo
SOURCE_LOGO = 'app/static/images/logos/TRANSPRNCY 2.png'
OUTPUT_DIR = 'app/static/images/icons'

# Icon sizes to generate
SIZES = [
    (72, 72),
    (96, 96),
    (128, 128),
    (144, 144),
    (152, 152),
    (192, 192),
    (384, 384),
    (512, 512),
]

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load source image
try:
    logo = Image.open(SOURCE_LOGO).convert('RGBA')
    print(f"✓ Loaded source image: {SOURCE_LOGO}")
    print(f"  Original size: {logo.size}")
    print()
    
    # Generate each size
    for width, height in SIZES:
        # Create a new image with transparent background
        icon = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        
        # Resize logo maintaining aspect ratio
        logo_resized = logo.copy()
        logo_resized.thumbnail((width, height), Image.Resampling.LANCZOS)
        
        # Center the logo
        offset = ((width - logo_resized.width) // 2, 
                  (height - logo_resized.height) // 2)
        icon.paste(logo_resized, offset, logo_resized)
        
        # Save icon
        output_path = os.path.join(OUTPUT_DIR, f'icon-{width}x{height}.png')
        icon.save(output_path, 'PNG')
        print(f"✓ Generated: icon-{width}x{height}.png")
    
    print()
    
    # Generate Apple Touch Icon (180x180)
    apple_icon = Image.new('RGBA', (180, 180), (0, 0, 0, 0))
    logo_apple = logo.copy()
    logo_apple.thumbnail((180, 180), Image.Resampling.LANCZOS)
    offset = ((180 - logo_apple.width) // 2, (180 - logo_apple.height) // 2)
    apple_icon.paste(logo_apple, offset, logo_apple)
    apple_path = os.path.join(OUTPUT_DIR, 'apple-touch-icon.png')
    apple_icon.save(apple_path, 'PNG')
    print(f"✓ Generated: apple-touch-icon.png")
    
    # Generate favicon (32x32) - PNG version
    favicon_png = logo.copy()
    favicon_png.thumbnail((32, 32), Image.Resampling.LANCZOS)
    
    # Create 32x32 centered image
    favicon_icon = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    offset = ((32 - favicon_png.width) // 2, (32 - favicon_png.height) // 2)
    favicon_icon.paste(favicon_png, offset, favicon_png)
    
    favicon_path_png = os.path.join(OUTPUT_DIR, 'icon-32x32.png')
    favicon_icon.save(favicon_path_png, 'PNG')
    print(f"✓ Generated: icon-32x32.png")
    
    # Generate .ico file (multi-resolution)
    favicon_path_ico = os.path.join(OUTPUT_DIR, 'favicon.ico')
    # Create 16x16 and 32x32 for .ico
    icon_16 = logo.copy()
    icon_16.thumbnail((16, 16), Image.Resampling.LANCZOS)
    icon_16_centered = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    offset_16 = ((16 - icon_16.width) // 2, (16 - icon_16.height) // 2)
    icon_16_centered.paste(icon_16, offset_16, icon_16)
    
    favicon_icon.save(favicon_path_ico, format='ICO', sizes=[(16, 16), (32, 32)])
    print(f"✓ Generated: favicon.ico")
    
    print()
    print("=" * 60)
    print("✅ All icons generated successfully!")
    print("=" * 60)
    print(f"\nTotal icons created: {len(SIZES) + 3}")
    
except FileNotFoundError:
    print(f"❌ Error: Source logo not found at {SOURCE_LOGO}")
    print("   Please ensure the logo file exists.")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
