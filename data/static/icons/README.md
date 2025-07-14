# PWA Icons Directory

This directory contains the icon files for the Progressive Web App (PWA) functionality.

## Required Icons (as defined in manifest.json):

- `icon-192x192.png` - Standard Android icon
- `icon-512x512.png` - Large Android icon  
- `favicon-16x16.png` - Browser favicon (small)
- `favicon-32x32.png` - Browser favicon (medium)
- `apple-touch-icon.png` - Apple touch icon (180x180)
- `android-chrome-192x192.png` - Android Chrome icon
- `android-chrome-512x512.png` - Android Chrome icon (large)
- `maskable-icon-512x512.png` - Maskable icon for adaptive icons

## Icon Specifications:

1. **Standard Icons (192x192, 512x512)**:
   - Should have the Video Transcriber logo/brand
   - Transparent or solid background
   - Good contrast for visibility

2. **Maskable Icons**:
   - Include safe zone (80% of icon area)
   - Background should extend to edges
   - Icon content centered in safe zone

3. **Apple Touch Icon**:
   - 180x180 pixels
   - Rounded corners will be applied automatically
   - No transparency (Apple adds its own background)

## Creating Icons:

You can create these icons using:
- Design tools (Figma, Sketch, Photoshop)
- Online PWA icon generators
- Command line tools like ImageMagick

Example ImageMagick commands:
```bash
# Resize a base icon to different sizes
convert icon-base.png -resize 192x192 icon-192x192.png
convert icon-base.png -resize 512x512 icon-512x512.png
```

## Placeholder Icons:

Until custom icons are created, you can use placeholder services:
- https://via.placeholder.com/192x192/007bff/ffffff?text=VT
- https://via.placeholder.com/512x512/007bff/ffffff?text=VT

The PWA will work with placeholder icons, but custom branded icons provide a better user experience.
