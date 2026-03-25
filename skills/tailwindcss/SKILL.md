# Skill : TailwindCSS

## Objectif

Ce skill présente les bonnes pratiques pour utiliser TailwindCSS efficacement. Couvre la configuration, les composants, la réactivité et l'optimisation.

## Quand utiliser ce skill

- Création d'un nouveau projet Tailwind
- Refactoring de CSS legacy
- Création de composants réutilisables
- Optimisation des performances CSS

## Installation et configuration

### Installation de base

```bash
# Via npm
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# Via CDN (développement uniquement)
# <script src="https://cdn.tailwindcss.com"></script>
```

### Configuration (tailwind.config.js)

```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/**/*.{html,js,jsx,ts,tsx,vue}',
    './templates/**/*.html',
    './apps/**/templates/**/*.html',
  ],
  theme: {
    extend: {
      // Couleurs personnalisées
      colors: {
        brand: {
          50: '#eff6ff',
          100: '#dbeafe',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          900: '#1e3a8a',
        },
      },
      // Typography
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Poppins', 'sans-serif'],
      },
      // Spacing
      spacing: {
        '128': '32rem',
        '144': '36rem',
      },
      // Breakpoints personnalisés
      screens: {
        'xs': '475px',
        '3xl': '1920px',
      },
      // Animations
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.5s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    require('@tailwindcss/aspect-ratio'),
  ],
}
```

### CSS de base (input.css)

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Couche base : styles par défaut */
@layer base {
  html {
    @apply antialiased;
  }
  
  body {
    @apply font-sans text-gray-900 bg-gray-50;
  }
  
  h1 {
    @apply text-4xl font-bold tracking-tight;
  }
  
  h2 {
    @apply text-3xl font-semibold tracking-tight;
  }
  
  a {
    @apply text-brand-600 hover:text-brand-700;
  }
}

/* Couche components : composants réutilisables */
@layer components {
  .btn {
    @apply inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors duration-200;
  }
  
  .btn-primary {
    @apply btn bg-brand-600 text-white hover:bg-brand-700 focus:ring-brand-500;
  }
  
  .btn-secondary {
    @apply btn bg-white text-gray-700 border-gray-300 hover:bg-gray-50 focus:ring-brand-500;
  }
  
  .card {
    @apply bg-white rounded-lg shadow-md overflow-hidden;
  }
  
  .input {
    @apply block w-full rounded-md border-gray-300 shadow-sm focus:border-brand-500 focus:ring-brand-500 sm:text-sm;
  }
}

/* Couche utilities : utilitaires personnalisés */
@layer utilities {
  .text-balance {
    text-wrap: balance;
  }
  
  .scrollbar-hide {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
  
  .scrollbar-hide::-webkit-scrollbar {
    display: none;
  }
}
```

## Bonnes pratiques fondamentales

### 1. Approche utility-first

```html
<!-- ❌ Mauvais - classes sémantiques traditionnelles -->
<div class="card">
  <div class="card-header">
    <h3 class="card-title">Titre</h3>
  </div>
  <div class="card-body">
    <p class="card-text">Contenu...</p>
  </div>
</div>

<!-- ✅ Bon - utilitaires Tailwind -->
<div class="bg-white rounded-lg shadow-md overflow-hidden">
  <div class="px-6 py-4 border-b border-gray-200">
    <h3 class="text-lg font-semibold text-gray-900">Titre</h3>
  </div>
  <div class="px-6 py-4">
    <p class="text-gray-600">Contenu...</p>
  </div>
</div>
```

### 2. Composants avec @apply

```html
<!-- ❌ Mauvais - duplication de classes -->
<button class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
  Bouton 1
</button>
<button class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
  Bouton 2
</button>

<!-- ✅ Bon - extraire en composant -->
<!-- Dans le HTML -->
<button class="btn-primary">Bouton 1</button>
<button class="btn-primary">Bouton 2</button>

<!-- Dans input.css -->
@layer components {
  .btn-primary {
    @apply px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors;
  }
}
```

### 3. Gestion responsive

```html
<!-- Mobile-first : classes sans préfixe = mobile -->
<!-- sm: = small (640px+) -->
<!-- md: = medium (768px+) -->
<!-- lg: = large (1024px+) -->
<!-- xl: = extra large (1280px+) -->

<!-- Exemple 1 : grille responsive -->
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
  <div class="bg-white p-4 rounded-lg shadow">Item 1</div>
  <div class="bg-white p-4 rounded-lg shadow">Item 2</div>
  <div class="bg-white p-4 rounded-lg shadow">Item 3</div>
</div>

<!-- Exemple 2 : taille de texte responsive -->
<h1 class="text-2xl md:text-3xl lg:text-4xl font-bold">
  Titre adaptatif
</h1>

<!-- Exemple 3 : layout responsive -->
<div class="flex flex-col md:flex-row gap-4">
  <aside class="w-full md:w-64 lg:w-80">
    <!-- Sidebar -->
  </aside>
  <main class="flex-1">
    <!-- Contenu principal -->
  </main>
</div>
```

### 4. Dark mode

```javascript
// tailwind.config.js
module.exports = {
  darkMode: 'class', // ou 'media' pour le mode système
  // ...
}
```

```html
<!-- Mode clair par défaut, dark: pour le mode sombre -->
<body class="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
  <div class="bg-white dark:bg-gray-800 shadow-lg dark:shadow-gray-900/50">
    <h2 class="text-gray-900 dark:text-white">Titre</h2>
    <p class="text-gray-600 dark:text-gray-400">Description</p>
  </div>
  
  <!-- Bouton toggle -->
  <button 
    onclick="document.documentElement.classList.toggle('dark')"
    class="p-2 rounded-lg bg-gray-200 dark:bg-gray-700"
  >
    🌓
  </button>
</body>
```

## Composants courants

### Layout

```html
<!-- Container centré avec padding responsive -->
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
  <!-- Contenu -->
</div>

<!-- Grille avec gap -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  <div>Item 1</div>
  <div>Item 2</div>
  <div>Item 3</div>
</div>

<!-- Flexbox commun -->
<div class="flex items-center justify-between gap-4">
  <div>Left</div>
  <div>Right</div>
</div>

<!-- Sidebar layout -->
<div class="flex min-h-screen">
  <aside class="w-64 bg-gray-800 text-white hidden md:block">
    <!-- Sidebar -->
  </aside>
  <main class="flex-1 p-6">
    <!-- Main content -->
  </main>
</div>
```

### Formulaires

```html
<!-- Formulaire avec Tailwind Forms plugin -->
<form class="space-y-6 max-w-lg">
  <!-- Input text -->
  <div>
    <label for="email" class="block text-sm font-medium text-gray-700">
      Email
    </label>
    <div class="mt-1">
      <input 
        type="email" 
        id="email"
        class="block w-full rounded-md border-gray-300 shadow-sm focus:border-brand-500 focus:ring-brand-500 sm:text-sm"
        placeholder="you@example.com"
      >
    </div>
  </div>
  
  <!-- Select -->
  <div>
    <label for="country" class="block text-sm font-medium text-gray-700">
      Pays
    </label>
    <select 
      id="country"
      class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-brand-500 focus:ring-brand-500 sm:text-sm"
    >
      <option>France</option>
      <option>Belgique</option>
      <option>Suisse</option>
    </select>
  </div>
  
  <!-- Checkbox group -->
  <div class="space-y-2">
    <div class="flex items-center">
      <input 
        type="checkbox" 
        id="newsletter"
        class="h-4 w-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500"
      >
      <label for="newsletter" class="ml-2 block text-sm text-gray-900">
        S'abonner à la newsletter
      </label>
    </div>
  </div>
  
  <!-- Radio group -->
  <div class="space-y-2">
    <label class="text-sm font-medium text-gray-700">Type de compte</label>
    <div class="flex items-center space-x-4">
      <div class="flex items-center">
        <input 
          type="radio" 
          name="account-type"
          value="personal"
          class="h-4 w-4 border-gray-300 text-brand-600 focus:ring-brand-500"
        >
        <label class="ml-2 text-sm text-gray-900">Personnel</label>
      </div>
      <div class="flex items-center">
        <input 
          type="radio" 
          name="account-type"
          value="business"
          class="h-4 w-4 border-gray-300 text-brand-600 focus:ring-brand-500"
        >
        <label class="ml-2 text-sm text-gray-900">Business</label>
      </div>
    </div>
  </div>
  
  <!-- Boutons -->
  <div class="flex justify-end space-x-3">
    <button type="button" class="btn-secondary">
      Annuler
    </button>
    <button type="submit" class="btn-primary">
      Enregistrer
    </button>
  </div>
</form>
```

### Navigation

```html
<!-- Navbar responsive -->
<nav class="bg-white shadow">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="flex justify-between h-16">
      <!-- Logo -->
      <div class="flex items-center">
        <a href="/" class="text-xl font-bold text-brand-600">
          MonApp
        </a>
      </div>
      
      <!-- Desktop menu -->
      <div class="hidden md:flex items-center space-x-8">
        <a href="/" class="text-gray-600 hover:text-gray-900">Accueil</a>
        <a href="/features" class="text-gray-600 hover:text-gray-900">Fonctionnalités</a>
        <a href="/pricing" class="text-gray-600 hover:text-gray-900">Tarifs</a>
        <a href="/login" class="btn-primary">Connexion</a>
      </div>
      
      <!-- Mobile menu button -->
      <div class="flex items-center md:hidden">
        <button type="button" class="text-gray-600 hover:text-gray-900">
          <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
          </svg>
        </button>
      </div>
    </div>
  </div>
</nav>
```

### Cards

```html
<!-- Card simple -->
<div class="bg-white rounded-lg shadow-md overflow-hidden">
  <img src="image.jpg" alt="" class="w-full h-48 object-cover">
  <div class="p-6">
    <h3 class="text-lg font-semibold text-gray-900 mb-2">Titre</h3>
    <p class="text-gray-600 mb-4">Description du contenu...</p>
    <a href="#" class="text-brand-600 hover:text-brand-700 font-medium">
      En savoir plus →
    </a>
  </div>
</div>

<!-- Card avec actions -->
<div class="bg-white rounded-lg shadow-md p-6">
  <div class="flex items-start justify-between">
    <div>
      <h3 class="text-lg font-semibold text-gray-900">Projet Alpha</h3>
      <p class="text-sm text-gray-500 mt-1">Mis à jour il y a 2 heures</p>
    </div>
    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
      Actif
    </span>
  </div>
  <div class="mt-4 flex space-x-3">
    <button class="btn-secondary text-sm">Modifier</button>
    <button class="text-red-600 hover:text-red-800 text-sm font-medium">
      Supprimer
    </button>
  </div>
</div>
```

### Tableaux

```html
<div class="overflow-x-auto">
  <table class="min-w-full divide-y divide-gray-200">
    <thead class="bg-gray-50">
      <tr>
        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
          Nom
        </th>
        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
          Email
        </th>
        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
          Statut
        </th>
        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
          Actions
        </th>
      </tr>
    </thead>
    <tbody class="bg-white divide-y divide-gray-200">
      <tr>
        <td class="px-6 py-4 whitespace-nowrap">
          <div class="flex items-center">
            <div class="h-10 w-10 rounded-full bg-gray-300"></div>
            <div class="ml-4">
              <div class="text-sm font-medium text-gray-900">John Doe</div>
            </div>
          </div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
          john@example.com
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
          <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
            Actif
          </span>
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
          <button class="text-brand-600 hover:text-brand-900">Modifier</button>
        </td>
      </tr>
    </tbody>
  </table>
</div>
```

### Modals

```html
<!-- Modal avec backdrop -->
<div class="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
  <!-- Backdrop -->
  <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
    <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true"></div>
    <span class="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
    
    <!-- Modal panel -->
    <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
      <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
        <div class="sm:flex sm:items-start">
          <div class="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100 sm:mx-0 sm:h-10 sm:w-10">
            <svg class="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
            </svg>
          </div>
          <div class="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
            <h3 class="text-lg leading-6 font-medium text-gray-900" id="modal-title">
              Confirmer la suppression
            </h3>
            <div class="mt-2">
              <p class="text-sm text-gray-500">
                Êtes-vous sûr de vouloir supprimer cet élément ? Cette action est irréversible.
              </p>
            </div>
          </div>
        </div>
      </div>
      <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
        <button type="button" class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none sm:ml-3 sm:w-auto sm:text-sm">
          Supprimer
        </button>
        <button type="button" class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm">
          Annuler
        </button>
      </div>
    </div>
  </div>
</div>
```

## Techniques avancées

### Groupes et conditions

```html
<!-- Group hover -->
<div class="group relative">
  <img src="photo.jpg" class="w-full">
  <div class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-50 transition-all duration-300">
    <div class="opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center h-full">
      <button class="text-white border border-white px-4 py-2">Voir</button>
    </div>
  </div>
</div>

<!-- Peer pour les formulaires -->
<div class="relative">
  <input 
    type="text" 
    id="floating_input"
    class="peer block w-full appearance-none rounded-lg border border-gray-300 bg-transparent px-4 py-2.5 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-0"
    placeholder=" "
  >
  <label 
    for="floating_input"
    class="absolute left-4 top-2.5 z-10 origin-[0] -translate-y-6 scale-75 transform text-sm text-gray-500 duration-300 peer-placeholder-shown:translate-y-0 peer-placeholder-shown:scale-100 peer-focus:-translate-y-6 peer-focus:scale-75 peer-focus:text-brand-600"
  >
    Nom d'utilisateur
  </label>
</div>

<!-- Arbitrary values -->
<div class="w-[123px] h-[calc(100vh-4rem)] top-[117px]">
  <!-- Valeurs arbitraires avec [] -->
</div>
```

### Arbitrary properties

```html
<!-- Propriétés CSS arbitraires -->
<div class="[mask-image:linear-gradient(black,transparent)]">
  Contenu masqué
</div>

<div class="[&:nth-child(3)]:underline">
  Troisième élément souligné
</div>
```

### Plugins utiles

```javascript
// tailwind.config.js
module.exports = {
  plugins: [
    // Forms - reset des styles de formulaires
    require('@tailwindcss/forms'),
    
    // Typography - styles pour contenu riche (articles, blogs)
    require('@tailwindcss/typography'),
    
    // Aspect ratio - ratios d'aspect
    require('@tailwindcss/aspect-ratio'),
    
    // Line clamp - limiter le nombre de lignes
    require('@tailwindcss/line-clamp'),
    
    // Container queries
    require('@tailwindcss/container-queries'),
  ],
}
```

```html
<!-- Typography plugin -->
<article class="prose prose-lg prose-slate max-w-none">
  <!-- Contenu avec styles typographiques automatiques -->
  <h1>Titre</h1>
  <p>Paragraphe avec <strong>gras</strong> et <em>italique</em>.</p>
  <blockquote>Citation...</blockquote>
</article>

<!-- Aspect ratio plugin -->
<div class="aspect-w-16 aspect-h-9">
  <iframe src="video.mp4" class="w-full h-full"></iframe>
</div>

<!-- Line clamp plugin -->
<p class="line-clamp-3">
  Ce texte sera limité à 3 lignes maximum...
</p>

<!-- Container queries -->
<div class="@container">
  <div class="@lg:grid-cols-3 @md:grid-cols-2 grid-cols-1">
    <!-- Responsive basé sur le conteneur, pas la viewport -->
  </div>
</div>
```

## Intégration avec frameworks

### Django

```html
<!-- templates/base.html -->
{% load static %}
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}Mon Site{% endblock %}</title>
  <link rel="stylesheet" href="{% static 'css/output.css' %}">
</head>
<body class="bg-gray-50">
  {% include 'includes/navbar.html' %}
  
  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    {% block content %}{% endblock %}
  </main>
  
  {% include 'includes/footer.html' %}
</body>
</html>
```

```python
# forms.py avec Tailwind classes
from django import forms

class ContactForm(forms.Form):
    name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-brand-500 focus:ring-brand-500 sm:text-sm'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-brand-500 focus:ring-brand-500 sm:text-sm'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-brand-500 focus:ring-brand-500 sm:text-sm',
            'rows': 4
        })
    )
```

### React / Vue / Angular

```jsx
// React avec Tailwind
function Button({ variant = 'primary', children, ...props }) {
  const baseClasses = 'px-4 py-2 rounded font-medium transition-colors';
  
  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700',
    secondary: 'bg-gray-200 text-gray-800 hover:bg-gray-300',
    danger: 'bg-red-600 text-white hover:bg-red-700',
  };
  
  return (
    <button 
      className={`${baseClasses} ${variantClasses[variant]}`}
      {...props}
    >
      {children}
    </button>
  );
}

// Vue avec Tailwind
<template>
  <button 
    :class="[
      'px-4 py-2 rounded font-medium transition-colors',
      variant === 'primary' && 'bg-blue-600 text-white hover:bg-blue-700',
      variant === 'secondary' && 'bg-gray-200 text-gray-800 hover:bg-gray-300',
    ]"
  >
    <slot />
  </button>
</template>
```

## Optimisation et production

### Purge CSS

```javascript
// tailwind.config.js
module.exports = {
  content: [
    './src/**/*.{js,jsx,ts,tsx,vue,html}',
    './templates/**/*.html',
    './apps/**/templates/**/*.html',
  ],
  // Purge CSS supprime automatiquement les classes non utilisées
}
```

### Minification

```bash
# Production build
npx tailwindcss -i ./src/input.css -o ./dist/output.css --minify

# Watch mode développement
npx tailwindcss -i ./src/input.css -o ./dist/output.css --watch
```

### Just-in-Time (JIT) mode

```javascript
// Activé par défaut dans Tailwind v3+
// Génère les styles à la volée, très rapide
module.exports = {
  mode: 'jit', // Plus nécessaire en v3+
  content: ['./src/**/*.{html,js}'],
}
```

## Checklist

### Configuration
- [ ] tailwind.config.js personnalisé avec les couleurs de marque
- [ ] Content paths correctement configurés
- [ ] Plugins nécessaires installés
- [ ] Dark mode configuré si nécessaire

### Développement
- [ ] Approche mobile-first
- [ ] Utiliser les classes utilitaires, pas de CSS custom
- [ ] Extraire les patterns récurrents avec @apply
- [ ] Tester en responsive à chaque modification

### Production
- [ ] Build de production avec --minify
- [ ] Purge CSS fonctionne (vérifier la taille du fichier)
- [ ] Pas de classes arbitraires non utilisées
- [ ] Images optimisées

## Ressources

- [Documentation Tailwind](https://tailwindcss.com/docs)
- [Tailwind UI](https://tailwindui.com/) - Composants officiels payants
- [Tailwind Components](https://tailwindcomponents.com/) - Composants communautaire
- [Tailwind Cheat Sheet](https://nerdcave.com/tailwind-cheat-sheet)
- [Headless UI](https://headlessui.com/) - Composants sans style
- [Heroicons](https://heroicons.com/) - Icônes SVG gratuites
