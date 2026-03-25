# TailwindCSS - Démarrage Rapide

## Installation

```bash
# npm
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# CDN (développement uniquement)
<script src="https://cdn.tailwindcss.com"></script>
```

## Configuration minimale

```javascript
// tailwind.config.js
module.exports = {
  content: [
    './src/**/*.{html,js}',
    './templates/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          500: '#3b82f6',
          600: '#2563eb',
        },
      },
    },
  },
  plugins: [],
}
```

```css
/* input.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer components {
  .btn {
    @apply px-4 py-2 rounded font-medium transition-colors;
  }
  .btn-primary {
    @apply btn bg-brand-600 text-white hover:bg-brand-700;
  }
}
```

## Commandes

```bash
# Build développement
npx tailwindcss -i ./src/input.css -o ./dist/output.css --watch

# Build production
npx tailwindcss -i ./src/input.css -o ./dist/output.css --minify
```

## Patterns courants

### Responsive

```html
<!-- Mobile-first : classes sans préfixe = mobile -->
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
  <div>Item</div>
  <div>Item</div>
  <div>Item</div>
</div>

<!-- Taille de texte responsive -->
<h1 class="text-2xl md:text-3xl lg:text-4xl">Titre</h1>
```

### Composants

```html
<!-- Bouton -->
<button class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
  Cliquez
</button>

<!-- Card -->
<div class="bg-white rounded-lg shadow-md p-6">
  <h3 class="text-lg font-semibold">Titre</h3>
  <p class="text-gray-600 mt-2">Contenu...</p>
</div>

<!-- Formulaire -->
<input class="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500">
```

### Dark Mode

```html
<div class="bg-white dark:bg-gray-800 text-gray-900 dark:text-white">
  Contenu
</div>
```

## Checklist

- [ ] Configuration content paths correcte
- [ ] Approche mobile-first
- [ ] Classes utilitaires, pas de CSS custom
- [ ] Tester responsive à chaque modification
- [ ] Build production avec --minify

## Ressources

- [Tailwind Docs](https://tailwindcss.com/docs)
- [Cheat Sheet](https://nerdcave.com/tailwind-cheat-sheet)
- [Heroicons](https://heroicons.com/)
