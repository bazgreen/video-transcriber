# Video Transcriber - Unified Design System

## 🎨 Overview

The Video Transcriber application now uses a unified design system that provides consistent styling, components, and user experience across all pages.

## 📁 File Structure

```
data/
├── static/
│   ├── css/
│   │   └── app.css          # Main CSS framework
│   └── js/
│       └── app.js           # Common JavaScript utilities
└── templates/
    ├── base.html            # Base template that all pages extend
    ├── index.html           # Main upload page
    ├── sessions.html        # Session listing page
    ├── config.html          # Keyword configuration page
    └── auth/
        ├── login.html       # Login page
        ├── register.html    # Registration page
        ├── profile.html     # User profile page
        └── change_password.html
```

## 🧩 Design Components

### CSS Variables
The design system uses CSS custom properties (variables) for consistency:

- **Colors**: Primary gradient (#667eea to #764ba2), success, danger, warning, info
- **Typography**: System fonts with defined scales
- **Spacing**: Consistent spacing scale (xs, sm, md, lg, xl, 2xl, 3xl)
- **Shadows**: Elevation system with multiple shadow levels
- **Border Radius**: Consistent radius scale

### Layout Patterns

1. **Centered Layout** (`layout-centered`)
   - Full viewport height with centered content
   - Used for: Home page, auth pages, config page
   - Gradient background

2. **Full Layout** (`layout-full`)
   - Full-width layout with header
   - Used for: Sessions page, results pages
   - Gray background with header navigation

### Container Types

- **`.container`**: Standard centered container (600px max-width)
- **`.container-wide`**: Wider container (800px max-width)  
- **`.container-full`**: Full-width container (1200px max-width)
- **`.auth-container`**: Authentication forms (400px max-width)

### Component Library

#### Navigation
- **`.header`**: Main header with gradient background
- **`.nav-buttons`**: Header navigation buttons
- **`.nav-links-inline`**: Inline navigation links for page content

#### Forms
- **`.form-group`**: Form field wrapper
- **`.form-control`**: Input/select styling
- **`.form-check`**: Checkbox/radio wrapper
- **`.form-errors`**: Error message styling

#### Buttons
- **`.btn`**: Base button class
- **`.btn-primary`**: Primary action button (gradient)
- **`.btn-secondary`**: Secondary button
- **`.btn-success`**: Success/confirm button
- **`.btn-danger`**: Delete/cancel button
- **`.btn-outline`**: Outlined button
- **`.btn-full`**: Full-width button
- **`.btn-sm/.btn-lg`**: Size variations

#### Cards
- **`.card`**: Base card component
- **`.card-header/.card-body/.card-footer`**: Card sections

#### Alerts
- **`.alert`**: Base alert class
- **`.alert-success/.alert-error/.alert-warning/.alert-info`**: Alert types

#### Upload Components
- **`.upload-area`**: File drop zone
- **`.upload-content`**: Upload area content
- **`.file-queue`**: File list container

#### Progress Components
- **`.progress-bar`**: Progress bar container
- **`.progress-fill`**: Progress indicator
- **`.loading-spinner`**: Loading animation

### Typography Scale

- **Page Title**: `page-title` class (large, centered)
- **Page Subtitle**: `page-subtitle` class (descriptive text)
- **Section Title**: `section-title` class (section headers)
- **Auth Header**: `auth-header` class (authentication forms)

## 🚀 JavaScript Utilities

The `app.js` file provides common utilities:

### Global Object: `VideoTranscriber`

#### Message System
```javascript
VideoTranscriber.showMessage('Success!', 'success');
VideoTranscriber.showMessage('Error occurred', 'error');
```

#### API Helpers
```javascript
const data = await VideoTranscriber.api.get('/api/endpoint');
await VideoTranscriber.api.post('/api/endpoint', { data });
```

#### Loading States
```javascript
VideoTranscriber.loading.show(button, 'Saving...');
VideoTranscriber.loading.hide(button);
```

#### Storage Helpers
```javascript
VideoTranscriber.storage.set('key', value);
const value = VideoTranscriber.storage.get('key', defaultValue);
```

#### DOM Helpers
```javascript
VideoTranscriber.dom.show(element);
VideoTranscriber.dom.hide(element);
VideoTranscriber.dom.create('div', { className: 'my-class' });
```

#### Utility Functions
```javascript
const size = VideoTranscriber.formatFileSize(bytes);
const duration = VideoTranscriber.formatDuration(seconds);
await VideoTranscriber.copyToClipboard(text);
```

## 📱 Responsive Design

The design system is mobile-first and includes:

- Responsive grid layouts
- Flexible navigation that stacks on mobile
- Touch-friendly button sizes
- Readable typography at all screen sizes
- Proper spacing for mobile interactions

### Breakpoints
- Mobile: < 768px
- Tablet: 768px - 1024px  
- Desktop: > 1024px

## 🎨 Color Palette

### Primary Colors
- **Primary**: #667eea (purple-blue)
- **Primary Dark**: #764ba2 (deep purple)
- **Gradient**: Linear gradient from primary to primary-dark

### Semantic Colors
- **Success**: #00b894 (green)
- **Danger**: #e74c3c (red)
- **Warning**: #f39c12 (orange)
- **Info**: #3498db (blue)

### Neutral Colors
- **Gray Scale**: 50-900 (from light to dark)
- **White**: #ffffff
- **Dark**: #333333

## 📐 Spacing System

Based on 0.25rem (4px) increments:

- **xs**: 0.25rem (4px)
- **sm**: 0.5rem (8px)
- **md**: 1rem (16px)
- **lg**: 1.5rem (24px)
- **xl**: 2rem (32px)
- **2xl**: 3rem (48px)
- **3xl**: 4rem (64px)

## 🔧 Usage Guidelines

### Template Structure
All pages should extend the base template:

```html
{% extends "base.html" %}

{% block title %}Page Title{% endblock %}
{% block body_class %}layout-centered{% endblock %}
{% set show_header = true %}

{% block content %}
<!-- Page content here -->
{% endblock %}
```

### CSS Class Naming
- Use semantic class names
- Follow the component.modifier pattern
- Use utility classes for spacing and layout
- Prefix custom classes with page-specific identifiers

### JavaScript Integration
- Use the global `VideoTranscriber` object for common functions
- Follow the established patterns for API calls and DOM manipulation
- Add page-specific scripts in the `{% block extra_js %}` section

## 🚀 Benefits

1. **Consistency**: All pages share the same visual language
2. **Maintainability**: Changes to the design system propagate across all pages
3. **Performance**: Single CSS file reduces HTTP requests
4. **Developer Experience**: Clear patterns and reusable components
5. **User Experience**: Familiar interface elements across the app
6. **Accessibility**: Consistent focus states, semantic HTML, proper contrast ratios

## 📝 Future Enhancements

- **Dark Mode**: CSS variables make it easy to add theme switching
- **Animation Library**: Add consistent transitions and animations
- **Component Documentation**: Interactive style guide
- **CSS Grid Integration**: Enhanced layout capabilities
- **Custom Properties**: More design tokens for fine-tuning

## 🎯 Getting Started

1. All new pages should extend `base.html`
2. Use existing CSS classes whenever possible
3. Add custom styles only when necessary
4. Follow the established naming conventions
5. Test on mobile devices
6. Use the JavaScript utilities for common tasks

The unified design system makes the Video Transcriber application more professional, consistent, and maintainable while providing a better user experience across all features.
