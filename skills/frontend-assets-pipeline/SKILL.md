# Skill : Frontend Assets Pipeline

## Objectif

Gérer, compiler et optimiser les assets frontend (CSS, JavaScript, images) pour les applications Django avec une intégration moderne et efficace.

## Quand utiliser ce skill

- Application avec besoin de CSS/JS avancé
- Utilisation de Tailwind CSS, SCSS, ou TypeScript
- Besoin de minification et d'optimisation
- Gestion moderne des dépendances npm

## Architecture

```
Source Files              Build Tools           Django Static
├─ src/css/               ├─ TailwindCSS    →   static/css/
│  └─ main.css            ├─ PostCSS            └─ app.min.css
├─ src/js/                ├─ ESBuild        →   static/js/
│  └─ app.js              └─ Terser             └─ app.min.js
└─ src/images/                                  →   static/images/
```

## Configuration moderne (2024)

### 1. Tailwind CSS + npm scripts

```bash
# Initialisation
npm init -y
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

```javascript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './**/templates/**/*.html',
    './static/src/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          900: '#1e3a8a',
        },
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}
```

```css
/* static/src/css/main.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Composants personnalisés */
@layer components {
  .btn-primary {
    @apply px-4 py-2 bg-primary-500 text-white rounded-lg 
           hover:bg-primary-600 transition-colors;
  }
  
  .card {
    @apply bg-white rounded-lg shadow-md p-6;
  }
}

/* Utilitaires personnalisés */
@layer utilities {
  .text-shadow {
    text-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }
}
```

```json
// package.json
{
  "scripts": {
    "dev": "tailwindcss -i ./static/src/css/main.css -o ./static/css/app.css --watch",
    "build": "tailwindcss -i ./static/src/css/main.css -o ./static/css/app.css --minify",
    "build:js": "esbuild static/src/js/app.js --bundle --minify --outfile=static/js/app.js",
    "build:all": "npm run build && npm run build:js",
    "watch": "npm-run-all --parallel watch:*",
    "watch:css": "tailwindcss -i ./static/src/css/main.css -o ./static/css/app.css --watch",
    "watch:js": "esbuild static/src/js/app.js --bundle --outfile=static/js/app.js --watch"
  },
  "devDependencies": {
    "@tailwindcss/forms": "^0.5.7",
    "@tailwindcss/typography": "^0.5.10",
    "autoprefixer": "^10.4.16",
    "esbuild": "^0.19.8",
    "npm-run-all": "^4.1.5",
    "postcss": "^8.4.32",
    "tailwindcss": "^3.3.6"
  }
}
```

### 2. JavaScript moderne avec ESBuild

```javascript
// static/src/js/app.js
import { createApp } from 'vue/dist/vue.esm-bundler.js';
import Alpine from 'alpinejs';

// Initialisation Alpine.js
document.addEventListener('alpine:init', () => {
  // Composants globaux
});

Alpine.start();

// HTMX support
import htmx from 'htmx.org';
window.htmx = htmx;

// Initialisations globales
document.addEventListener('DOMContentLoaded', () => {
  console.log('App initialized');
});

// Gestion des erreurs HTMX
document.body.addEventListener('htmx:error', (event) => {
  console.error('HTMX Error:', event.detail);
});

// Export pour usage global
window.Alpine = Alpine;
```

### 3. Configuration Django

```python
# settings.py
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Whitenoise pour servir les fichiers statiques
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    ...
]

# En production
if ENVIRONMENT == 'production':
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
else:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Collecte automatique (optionnel)
WHITENOISE_AUTOREFRESH = DEBUG
```

### 4. Template de base

```html
<!-- templates/base.html -->
{% load static %}
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}MyApp{% endblock %}</title>
    
    <!-- CSS compilé -->
    <link rel="stylesheet" href="{% static 'css/app.css' %}">
    
    {% block extra_css %}{% endblock %}
</head>
<body class="bg-gray-50 min-h-screen">
    <nav class="bg-white shadow-sm">
        <!-- Navigation -->
    </nav>
    
    <main class="container mx-auto px-4 py-8">
        {% block content %}{% endblock %}
    </main>
    
    <!-- JavaScript -->
    <script src="{% static 'js/app.js' %}" defer></script>
    
    {% block extra_js %}{% endblock %}
</body>
</html>
```

## Scripts utilitaires

### Script de build

```bash
#!/bin/bash
# scripts/build-assets.sh

set -e

echo "🏗️  Building frontend assets..."

# Installer dépendances si nécessaire
if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules/.package-lock.json" ]; then
    echo "📦 Installing npm dependencies..."
    npm install
fi

# Build CSS
echo "🎨 Building CSS..."
npm run build

# Build JS
echo "⚡ Building JavaScript..."
npm run build:js

# Optimiser les images (optionnel)
if command -v npx &> /dev/null; then
    echo "🖼️  Optimizing images..."
    npx imagemin static/src/images/* --out-dir=static/images/
fi

# Collecter les statics Django
echo "📥 Collecting Django static files..."
python manage.py collectstatic --noinput --clear

echo "✅ Build complete!"
```

### Watch mode

```bash
#!/bin/bash
# scripts/watch-assets.sh

echo "👀 Watching for changes..."
npm run watch
```

## Optimisation avancée

### 1. Purge CSS optimisée

```javascript
// tailwind.config.js
module.exports = {
  content: [
    './templates/**/*.html',
    './**/templates/**/*.html',
    './static/src/**/*.js',
  ],
  // Désactiver les classes non utilisées
  safelist: [
    'bg-red-500',
    'text-3xl',
    'lg:text-4xl',
    // Classes dynamiques
    {
      pattern: /bg-(red|green|blue)-(100|200|300)/,
    },
  ],
  theme: {
    // ...
  },
}
```

### 2. Lazy loading des images

```html
<!-- Template Django avec lazy loading -->
<img 
    src="{% static 'images/placeholder.png' %}"
    data-src="{{ article.image.url }}"
    alt="{{ article.title }}"
    class="lazy-image w-full h-64 object-cover"
    loading="lazy"
>

<script>
    // Lazy loading natif
    if ('loading' in HTMLImageElement.prototype) {
        const images = document.querySelectorAll('img[loading="lazy"]');
        images.forEach(img => {
            img.src = img.dataset.src;
        });
    } else {
        // Fallback pour anciens navigateurs
        import('lazysizes').then(lazySizes => {
            // lazysizes auto-initialise
        });
    }
</script>
```

### 3. Critical CSS

```javascript
// critical-css.js
const critical = require('critical');

critical.generate({
    base: 'static/',
    src: '../templates/index.html',
    target: 'css/critical.css',
    dimensions: [
        { width: 320, height: 568 },   // Mobile
        { width: 768, height: 1024 },  // Tablet
        { width: 1920, height: 1080 }, // Desktop
    ],
});
```

## Intégration CI/CD

```yaml
# .github/workflows/assets.yml
name: Build Assets

on:
  push:
    branches: [main]
    paths:
      - 'static/src/**'
      - 'package*.json'
      - 'tailwind.config.js'

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Build assets
        run: |
          npm run build
          npm run build:js
      
      - name: Commit built files
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add static/css/ static/js/
          git diff --quiet && git diff --staged --quiet || git commit -m "chore: build assets"
          git push
```

## Checklist Frontend Pipeline

### Setup
- [ ] Node.js et npm installés
- [ ] package.json configuré
- [ ] Tailwind CSS initialisé
- [ ] ESBuild configuré
- [ ] Scripts npm définis

### Développement
- [ ] `npm run watch` pour dev
- [ ] Hot reload fonctionnel
- [ ] Source maps activées
- [ ] Debug facilité

### Production
- [ ] Minification CSS/JS
- [ ] Compression Gzip/Brotli
- [ ] Cache headers configurés
- [ ] CDN (optionnel)
- [ ] Images optimisées

### Performance
- [ ] Purge CSS activée
- [ ] Lazy loading images
- [ ] Critical CSS (optionnel)
- [ ] Font loading optimisé

## Ressources

- [Tailwind CSS](https://tailwindcss.com/)
- [ESBuild](https://esbuild.github.io/)
- [PostCSS](https://postcss.org/)
- [Alpine.js](https://alpinejs.dev/)
- [HTMX](https://htmx.org/)
