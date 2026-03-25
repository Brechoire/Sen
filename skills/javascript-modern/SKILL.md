# Skill : JavaScript Moderne (ES2024/ES2025)

## Objectif

Ce skill présente les fonctionnalités et bonnes pratiques de JavaScript moderne (ECMAScript 2024 et ES2025). Couvre les nouvelles syntaxes, les patterns de développement et l'écosystème moderne.

## Quand utiliser ce skill

- Développement frontend moderne (Vanilla JS, React, Vue, Angular)
- Création d'applications Node.js
- Migration de code legacy vers JavaScript moderne
- Optimisation de performances JavaScript
- Écriture de code maintenable et type-safe

## Table des matières des versions

| Version | Nom | Date de sortie | Caractéristiques principales |
|---------|-----|----------------|------------------------------|
| ES2015 | ES6 | Juin 2015 | let/const, arrow functions, classes, modules |
| ES2016 | ES7 | Juin 2016 | Exponentiation operator, Array.prototype.includes |
| ES2017 | ES8 | Juin 2017 | async/await, Object.entries, Object.values |
| ES2018 | ES9 | Juin 2018 | Spread operator, Promise.finally, async iterators |
| ES2019 | ES10 | Juin 2019 | Array.flat, Object.fromEntries, trimStart/trimEnd |
| ES2020 | ES11 | Juin 2020 | BigInt, nullish coalescing, optional chaining |
| ES2021 | ES12 | Juin 2021 | Promise.any, logical assignment, numeric separators |
| ES2022 | ES13 | Juin 2022 | Class fields, at() method, top-level await |
| ES2023 | ES14 | Juin 2023 | Array.toSorted, toReversed, with, findLast |
| ES2024 | ES15 | Juin 2024 | GroupBy, Promise.withResolvers, ArrayBuffer.transfer |
| ES2025 | ES16 | Juin 2025 | Iterator helpers, Set operations, Regex extensions |

## Installation et configuration

### 1. Configuration Node.js

```bash
# Vérifier la version de Node.js
node --version

# Mettre à jour vers la dernière LTS
nvm install --lts
nvm use --lts

# Vérifier la compatibilité ES2024
node --eval "console.log(process.versions.v8)"
```

### 2. Configuration ESLint (recommandé)

```bash
# Installation
npm install --save-dev eslint @eslint/js
```

Configuration (eslint.config.js):

```javascript
import js from '@eslint/js';

export default [
  js.configs.recommended,
  {
    languageOptions: {
      ecmaVersion: 2024,
      sourceType: 'module',
      globals: {
        console: 'readonly',
        document: 'readonly',
        window: 'readonly',
      },
    },
    rules: {
      'no-unused-vars': 'warn',
      'no-console': 'off',
      'prefer-const': 'error',
      'no-var': 'error',
    },
  },
];
```

### 3. Configuration TypeScript (optionnel)

```bash
npm install --save-dev typescript @types/node
```

tsconfig.json:

```json
{
  "compilerOptions": {
    "target": "ES2024",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  }
}
```

## Fonctionnalités ES2024

### Object.groupBy() et Map.groupBy()

Groupe les éléments d'un tableau par clé.

```javascript
const inventory = [
  { name: 'pommes', type: 'fruit', quantity: 10 },
  { name: 'bananes', type: 'fruit', quantity: 5 },
  { name: 'carottes', type: 'legume', quantity: 20 },
];

// Grouper par type
const byType = Object.groupBy(inventory, item => item.type);
// {
//   fruit: [{ pommes }, { bananes }],
//   legume: [{ carottes }]
// }

// Grouper par condition
const enStock = Object.groupBy(inventory, item => 
  item.quantity > 10 ? 'suffisant' : 'faible'
);

// Avec Map.groupBy pour des clés complexes
const byRef = Map.groupBy(inventory, item => item.type);
```

### Promise.withResolvers()

Crée une promesse avec resolve et reject accessibles.

```javascript
// Avant
let resolve, reject;
const promise = new Promise((res, rej) => {
  resolve = res;
  reject = rej;
});

// Avec ES2024
const { promise, resolve, reject } = Promise.withResolvers();

// Cas d'usage : délais d'attente personnalisés
function delay(ms) {
  const { promise, resolve } = Promise.withResolvers();
  setTimeout(resolve, ms);
  return promise;
}

await delay(1000); // Attend 1 seconde
```

### ArrayBuffer et SharedArrayBuffer améliorés

```javascript
// Transférer un ArrayBuffer (détache la source)
const buffer1 = new ArrayBuffer(1024);
const buffer2 = buffer1.transfer();
// buffer1 est maintenant détaché, buffer2 contient les données

// Redimensionner un ArrayBuffer
const resizable = new ArrayBuffer(1024, { maxByteLength: 4096 });
resizable.resize(2048); // OK, car < maxByteLength
```

### Well-Formed Unicode Strings

```javascript
// Vérifier si une chaîne est bien formée Unicode
const bad = '\uD800'; // Surrogate isolé
console.log(bad.isWellFormed()); // false

// Convertir en chaîne bien formée
const fixed = bad.toWellFormed();
console.log(fixed); // Remplace par � (U+FFFD)
```

## Fonctionnalités ES2025 (Stage 4)

### Iterator Helpers

```javascript
const numbers = [1, 2, 3, 4, 5];

// map, filter, take, drop sur les itérateurs
const result = numbers
  .values()
  .filter(n => n % 2 === 0)
  .map(n => n * 2)
  .take(2)
  .toArray();
// [4, 8]

// Autres méthodes disponibles
const iterator = numbers.values();
iterator.every(n => n > 0);  // true
iterator.some(n => n > 4);   // true
iterator.find(n => n > 3);   // 4
iterator.reduce((a, b) => a + b); // 15
iterator.toArray();          // [1, 2, 3, 4, 5]
iterator.forEach(console.log);
```

### Set Operations

```javascript
const set1 = new Set([1, 2, 3]);
const set2 = new Set([2, 3, 4]);

// Union
const union = set1.union(set2);           // {1, 2, 3, 4}

// Intersection
const intersection = set1.intersection(set2); // {2, 3}

// Différence
const diff = set1.difference(set2);       // {1}

// Différence symétrique
const symDiff = set1.symmetricDifference(set2); // {1, 4}

// Sous-ensemble, sur-ensemble
set1.isSubsetOf(set2);        // false
set1.isSupersetOf(set2);      // false
set1.isDisjointFrom(set2);    // false
```

### Regex avec /v flag

```javascript
// Classes de caractères étendues
const regex = /[\p{Emoji}]/v;  // Correspond aux emojis

// Set operations dans les classes
const regex2 = /[a-z&&[^aeiou]]/v; // Consonnes uniquement
```

## Fonctionnalités récentes importantes (rappel)

### ES2023 : Nouvelles méthodes de tableau

```javascript
const arr = [3, 1, 4, 1, 5];

// toSorted (sans mutation)
const sorted = arr.toSorted(); // [1, 1, 3, 4, 5]
console.log(arr);              // [3, 1, 4, 1, 5] (inchangé)

// toReversed (sans mutation)
const reversed = arr.toReversed(); // [5, 1, 4, 1, 3]

// with (modifier un élément sans mutation)
const modified = arr.with(2, 99); // [3, 1, 99, 1, 5]

// findLast et findLastIndex
arr.findLast(n => n < 3);      // 1
arr.findLastIndex(n => n < 3); // 3
```

### ES2022 : Top-level await et class fields

```javascript
// Top-level await (modules ES)
const data = await fetch('/api/data').then(r => r.json());

// Class fields et private fields
class Counter {
  #count = 0;  // Private field
  
  static #instances = 0;  // Static private
  
  constructor() {
    Counter.#instances++;
  }
  
  increment() {
    this.#count++;
  }
  
  get count() {
    return this.#count;
  }
  
  static get instances() {
    return Counter.#instances;
  }
}

// Méthode at() pour l'indexation négative
const items = ['a', 'b', 'c'];
items.at(-1);  // 'c' (dernier élément)
items.at(-2);  // 'b' (avant-dernier)
```

### ES2020-2021 : Optional chaining et nullish coalescing

```javascript
const user = {
  profile: {
    name: 'John',
    settings: {
      theme: 'dark'
    }
  }
};

// Optional chaining (?.)
const theme = user?.profile?.settings?.theme; // 'dark'
const bio = user?.profile?.bio?.content;      // undefined (pas d'erreur)

// Nullish coalescing (??)
const value = null ?? 'default';      // 'default'
const value2 = 0 ?? 'default';        // 0 (pas 'default' comme avec ||)

// Logical assignment
let config = {};
config.theme ??= 'light';  // Assigne si null/undefined
config.count ||= 10;       // Assigne si falsy
config.debug &&= false;    // Assigne si truthy
```

## Patterns modernes

### 1. Module ES6+ (import/export)

```javascript
// math.js
export const PI = 3.14159;
export function add(a, b) { return a + b; }
export default class Calculator { }

// main.js
import Calculator, { PI, add } from './math.js';
import * as math from './math.js';
import { add as addition } from './math.js';

// Imports dynamiques
const module = await import('./math.js');
```

### 2. Destructuring et spread

```javascript
// Object destructuring
const { name, age = 25, profile: { email } = {} } = user;

// Array destructuring
const [first, second, ...rest] = [1, 2, 3, 4, 5];

// Nested destructuring
const { coords: { x, y } } = { coords: { x: 10, y: 20 } };

// Spread operator
const merged = { ...obj1, ...obj2 };
const combined = [...arr1, ...arr2];

// Rest parameters
function sum(...numbers) {
  return numbers.reduce((a, b) => a + b, 0);
}
```

### 3. Async/await patterns

```javascript
// Gestion d'erreurs moderne
async function fetchData() {
  try {
    const response = await fetch('/api/data');
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch:', error);
    throw error;
  }
}

// Parallel execution
const [users, posts, comments] = await Promise.all([
  fetchUsers(),
  fetchPosts(),
  fetchComments(),
]);

// Race with timeout
const data = await Promise.race([
  fetchData(),
  new Promise((_, reject) => 
    setTimeout(() => reject(new Error('Timeout')), 5000)
  ),
]);

// Promise.allSettled (tous les résultats, même erreurs)
const results = await Promise.allSettled([promise1, promise2, promise3]);
```

### 4. Générateurs et itérateurs

```javascript
// Générateur
function* fibonacci(n) {
  let [a, b] = [0, 1];
  for (let i = 0; i < n; i++) {
    yield a;
    [a, b] = [b, a + b];
  }
}

for (const num of fibonacci(10)) {
  console.log(num);
}

// Itérateur personnalisé
class Range {
  constructor(start, end) {
    this.start = start;
    this.end = end;
  }
  
  *[Symbol.iterator]() {
    for (let i = this.start; i <= this.end; i++) {
      yield i;
    }
  }
}

const range = new Range(1, 5);
console.log([...range]); // [1, 2, 3, 4, 5]
```

## Bonnes pratiques

### 1. Utiliser const par défaut

```javascript
// ✅ Bon
const PI = 3.14159;
const config = { theme: 'dark' };
let count = 0;

// ❌ Mauvais
var x = 10;
let y = 20;  // Si jamais réassigné
```

### 2. Préférer les fonctions fléchées pour les callbacks

```javascript
// ✅ Bon
const doubled = numbers.map(n => n * 2);
const sum = numbers.reduce((a, b) => a + b, 0);

// Pour les méthodes avec this, utiliser une fonction régulière
const obj = {
  value: 42,
  regularMethod() {
    setTimeout(() => {
      console.log(this.value); // 42 (this conservé)
    }, 100);
  },
};
```

### 3. Éviter les mutations

```javascript
// ❌ Mutation
arr.push(item);
obj.prop = value;

// ✅ Sans mutation (ES2023+)
const newArr = [...arr, item];
const newObj = { ...obj, prop: value };
const sortedArr = arr.toSorted(); // ES2023
```

### 4. Utiliser template literals

```javascript
// ❌ Concaténation
const message = 'Bonjour ' + name + ', vous avez ' + count + ' messages.';

// ✅ Template literal
const message = `Bonjour ${name}, vous avez ${count} messages.`;

// Tagged template literals
const sql = SQL`SELECT * FROM users WHERE id = ${userId}`;
```

### 5. Gestion d'erreurs avec Error Cause

```javascript
// ✅ ES2022 Error Cause
try {
  await fetchUserData();
} catch (error) {
  throw new Error('Failed to load user profile', { cause: error });
}

// Accès à la cause
} catch (error) {
  console.error(error.message);       // 'Failed to load user profile'
  console.error(error.cause);         // Erreur originale
}
```

## Intégration avec frameworks

### React (fonctionnel)

```jsx
// Hooks modernes
function UserProfile({ userId }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const controller = new AbortController();
    
    fetchUser(userId, { signal: controller.signal })
      .then(setUser)
      .catch(err => {
        if (err.name !== 'AbortError') {
          console.error(err);
        }
      })
      .finally(() => setLoading(false));
    
    return () => controller.abort();
  }, [userId]);
  
  if (loading) return <Spinner />;
  if (!user) return <Error message="User not found" />;
  
  return (
    <div className="profile">
      <h1>{user.name}</h1>
      <p>{user.bio ?? 'No bio available'}</p>
    </div>
  );
}
```

### Vue 3 (Composition API)

```vue
<script setup>
import { ref, computed, onMounted } from 'vue';

const users = ref([]);
const searchQuery = ref('');

const filteredUsers = computed(() => 
  users.value.filter(u => 
    u.name.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
);

const userGroups = computed(() =>
  Object.groupBy(filteredUsers.value, u => u.role)
);

onMounted(async () => {
  users.value = await fetchUsers();
});
</script>
```

### Node.js moderne

```javascript
// ES Modules natifs (package.json: "type": "module")
import { readFile } from 'node:fs/promises';
import { createServer } from 'node:http';

// Top-level await
const config = JSON.parse(await readFile('./config.json', 'utf8'));

// Server moderne
const server = createServer(async (req, res) => {
  try {
    const data = await processRequest(req);
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(data));
  } catch (error) {
    res.writeHead(500);
    res.end(JSON.stringify({ error: error.message }));
  }
});

server.listen(config.port);
```

## Checklist

### Configuration
- [ ] Node.js version récente (LTS recommandé)
- [ ] ESLint configuré avec ecmaVersion 2024
- [ ] TypeScript configuré si applicable
- [ ] Modules ES activés ("type": "module")

### Syntaxe moderne
- [ ] Utiliser const/let (pas var)
- [ ] Arrow functions pour les callbacks
- [ ] Template literals pour les chaînes
- [ ] Destructuring et spread operator
- [ ] Optional chaining et nullish coalescing

### Fonctionnalités récentes
- [ ] ES2024: Object.groupBy() / Map.groupBy()
- [ ] ES2024: Promise.withResolvers()
- [ ] ES2023: toSorted, toReversed, with (sans mutation)
- [ ] ES2022: Class fields et private fields (#)
- [ ] ES2020+: Async/await patterns

### Bonnes pratiques
- [ ] Pas de mutations sur les données
- [ ] Gestion d'erreurs appropriée
- [ ] Utiliser les itérateurs helpers (ES2025)
- [ ] Modules ES avec imports/exports
- [ ] AbortController pour les requêtes annulables

### Performance
- [ ] Lazy loading avec imports dynamiques
- [ ] Utiliser les Set operations (ES2025)
- [ ] Générateurs pour les grandes collections
- [ ] Éviter les fuites mémoire (cleanup dans useEffect)

## Ressources

- [MDN JavaScript Guide](https://developer.mozilla.org/fr/docs/Web/JavaScript/Guide)
- [ES2024 Specification](https://tc39.es/ecma262/2024/)
- [Node.js ES Modules](https://nodejs.org/api/esm.html)
- [Can I use - ES2024](https://caniuse.com/?search=es2024)
- [JavaScript.info](https://javascript.info/)
- [ESLint Configuration](https://eslint.org/docs/latest/use/configure/)

---

*Ce skill est maintenu à jour avec les dernières spécifications ECMAScript.*
