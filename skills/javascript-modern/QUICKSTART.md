# JavaScript Moderne - Quick Start

## Installation rapide

```bash
# Vérifier Node.js
node --version  # >= 18.x recommandé

# ESLint
npm install --save-dev eslint @eslint/js
```

## Table des versions ES

| Version | Fonctionnalités clés |
|---------|---------------------|
| ES2024 | `Object.groupBy()`, `Promise.withResolvers()`, `ArrayBuffer.transfer()` |
| ES2025 | Iterator helpers, Set operations (union, intersection, difference) |
| ES2023 | `toSorted()`, `toReversed()`, `with()`, `findLast()` |
| ES2022 | Class fields (`#private`), top-level await, `at()` |
| ES2020 | Optional chaining (`?.`), nullish coalescing (`??`) |

## Fonctionnalités ES2024

### Object.groupBy()

```javascript
const items = [
  { name: 'pomme', type: 'fruit' },
  { name: 'carotte', type: 'legume' },
];

const grouped = Object.groupBy(items, i => i.type);
// { fruit: [...], legume: [...] }
```

### Promise.withResolvers()

```javascript
const { promise, resolve, reject } = Promise.withResolvers();

// Utilisation typique : timeout personnalisé
function delay(ms) {
  const { promise, resolve } = Promise.withResolvers();
  setTimeout(resolve, ms);
  return promise;
}

await delay(1000);
```

### ArrayBuffer.transfer()

```javascript
const buffer1 = new ArrayBuffer(1024);
const buffer2 = buffer1.transfer();
// buffer1 est détaché, buffer2 contient les données
```

## Fonctionnalités ES2025

### Iterator Helpers

```javascript
const numbers = [1, 2, 3, 4, 5];

const result = numbers
  .values()
  .filter(n => n > 2)
  .map(n => n * 2)
  .toArray();
// [6, 8, 10]
```

### Set Operations

```javascript
const a = new Set([1, 2, 3]);
const b = new Set([2, 3, 4]);

a.union(b);              // {1, 2, 3, 4}
a.intersection(b);       // {2, 3}
a.difference(b);         // {1}
a.symmetricDifference(b); // {1, 4}
a.isSubsetOf(b);         // false
```

## Fonctionnalités essentielles (rappel)

### ES2023 - Méthodes sans mutation

```javascript
const arr = [3, 1, 2];

arr.toSorted();     // [1, 2, 3] - arr inchangé
arr.toReversed();   // [2, 1, 3] - arr inchangé
arr.with(1, 99);    // [3, 99, 2] - arr inchangé
arr.findLast(x => x < 3);      // 2
arr.findLastIndex(x => x < 3); // 2
```

### ES2022 - Class fields

```javascript
class Counter {
  #count = 0;           // Private field
  static #total = 0;    // Static private
  
  increment() {
    this.#count++;
    Counter.#total++;
  }
  
  get count() { return this.#count; }
}

// Indexation négative
[1, 2, 3].at(-1);  // 3
```

### ES2020 - Optional chaining & nullish

```javascript
// Optional chaining
const theme = user?.settings?.theme;

// Nullish coalescing
const value = null ?? 'default';  // 'default'
const zero = 0 ?? 'default';      // 0 (pas 'default'!)

// Logical assignment
config.theme ??= 'light';
config.count ||= 0;
```

## Configuration ESLint

```javascript
// eslint.config.js
import js from '@eslint/js';

export default [
  js.configs.recommended,
  {
    languageOptions: {
      ecmaVersion: 2024,
      sourceType: 'module',
    },
    rules: {
      'no-var': 'error',
      'prefer-const': 'error',
    },
  },
];
```

## Patterns modernes

### Modules ES

```javascript
// Named exports
export const PI = 3.14;
export function add(a, b) { return a + b; }

// Default export
export default class MyClass {}

// Imports
import MyClass, { PI, add } from './module.js';
import * as utils from './module.js';

// Dynamic import
const module = await import('./module.js');
```

### Destructuring

```javascript
// Object
const { name, age = 25 } = user;
const { profile: { email } = {} } = user;

// Array
const [first, second, ...rest] = arr;

// Spread
const merged = { ...obj1, ...obj2 };
const combined = [...arr1, ...arr2];
```

### Async/await

```javascript
// Gestion d'erreurs
async function fetchData() {
  try {
    const res = await fetch('/api/data');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error('Fetch failed:', err);
    throw err;
  }
}

// Parallélisme
const [users, posts] = await Promise.all([
  fetchUsers(),
  fetchPosts(),
]);

// Timeout
const data = await Promise.race([
  fetchData(),
  new Promise((_, reject) => 
    setTimeout(() => reject(new Error('Timeout')), 5000)
  ),
]);
```

## Bonnes pratiques

### ✅ Faire

```javascript
// const par défaut
const PI = 3.14159;
let count = 0;

// Arrow functions pour les callbacks
const doubled = numbers.map(n => n * 2);

// Template literals
const msg = `Hello ${name}`;

// Pas de mutations
const newArr = [...arr, item];
const newObj = { ...obj, prop: value };
```

### ❌ Éviter

```javascript
// var
var x = 10;

// Concaténation
const msg = 'Hello ' + name;

// Mutations
arr.push(item);
obj.prop = value;
```

## Intégration React

```jsx
function UserList() {
  const [users, setUsers] = useState([]);
  
  useEffect(() => {
    const controller = new AbortController();
    
    fetchUsers({ signal: controller.signal })
      .then(setUsers)
      .catch(err => {
        if (err.name !== 'AbortError') console.error(err);
      });
    
    return () => controller.abort();
  }, []);
  
  // Grouper avec ES2024
  const byRole = Object.groupBy(users, u => u.role);
  
  return (
    <div>
      {Object.entries(byRole).map(([role, group]) => (
        <section key={role}>
          <h2>{role}</h2>
          {group.map(user => <UserCard key={user.id} user={user} />)}
        </section>
      ))}
    </div>
  );
}
```

## Intégration Vue 3

```vue
<script setup>
import { ref, computed } from 'vue';

const users = ref([]);
const search = ref('');

const filtered = computed(() =>
  users.value.filter(u =>
    u.name.toLowerCase().includes(search.value.toLowerCase())
  )
);

// ES2024 groupBy
const groups = computed(() =>
  Object.groupBy(filtered.value, u => u.department)
);
</script>
```

## Checklist rapide

- [ ] Node.js LTS (v18+)
- [ ] ESLint avec ecmaVersion 2024
- [ ] `const` par défaut, `let` si réassigné
- [ ] Arrow functions pour callbacks
- [ ] Optional chaining (`?.`) et nullish (`??`)
- [ ] Pas de mutations (utiliser spread)
- [ ] ES2024: `Object.groupBy()` pour grouper
- [ ] ES2024: `Promise.withResolvers()` pour promesses manuelles
- [ ] ES2025: Iterator helpers (map, filter, take)
- [ ] ES2025: Set operations (union, intersection)
- [ ] Modules ES avec imports/exports
- [ ] Async/await avec gestion d'erreurs
- [ ] AbortController pour les fetch annulables

## Ressources

- [MDN JavaScript](https://developer.mozilla.org/fr/docs/Web/JavaScript)
- [Can I use](https://caniuse.com/)
- [Node.js ES Modules](https://nodejs.org/api/esm.html)
