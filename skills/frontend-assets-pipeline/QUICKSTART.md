# Frontend Assets Pipeline - Démarrage Rapide

## Installation (5 minutes)

```bash
# 1. Initialiser npm
npm init -y

# 2. Installer Tailwind CSS
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# 3. Installer ESBuild pour JS
npm install -D esbuild

# 4. Créer structure
mkdir -p static/src/css static/src/js static/css static/js
```

## Configuration rapide

```javascript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './**/templates/**/*.html',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

```css
/* static/src/css/main.css */
@tailwind base;
@tailwind components;
@tailwind utilities;
```

```javascript
// static/src/js/app.js
console.log('App loaded');
```

```json
// package.json (ajouter dans scripts)
{
  "scripts": {
    "dev": "tailwindcss -i ./static/src/css/main.css -o ./static/css/app.css --watch",
    "build": "tailwindcss -i ./static/src/css/main.css -o ./static/css/app.css --minify",
    "build:js": "esbuild static/src/js/app.js --bundle --minify --outfile=static/js/app.js"
  }
}
```

## Utilisation quotidienne

```bash
# Mode développement (watch)
npm run dev

# Build production
npm run build
npm run build:js

# Build complet
npm run build && npm run build:js
```

## Intégration Django

```python
# settings.py
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Whitenoise (middleware)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    ...
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

```html
<!-- templates/base.html -->
{% load static %}
<link rel="stylesheet" href="{% static 'css/app.css' %}">
<script src="{% static 'js/app.js' %}" defer></script>
```

## Checklist rapide

- [ ] `npm install` effectué
- [ ] `tailwind.config.js` créé
- [ ] Fichier CSS source créé
- [ ] Scripts npm configurés
- [ ] Template Django mis à jour
- [ ] Whitenoise installé et configuré

## Commandes essentielles

```bash
# Build en dev (watch)
npm run dev

# Build production
npm run build

# Build JS
npx esbuild static/src/js/app.js --bundle --minify --outfile=static/js/app.js

# Collecter les statics
python manage.py collectstatic --noinput
```
