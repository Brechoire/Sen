// Gestion du panier dynamique
class CartManager {
    constructor() {
        this.cartData = null;
        this.init();
    }

    init() {
        this.loadCartSummary();
        this.bindEvents();
    }

    bindEvents() {
        // Événements pour les boutons d'ajout au panier
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-add-to-cart]')) {
                e.preventDefault();
                const bookId = e.target.getAttribute('data-book-id');
                const quantity = e.target.getAttribute('data-quantity') || 1;
                this.addToCart(bookId, quantity);
            }
        });
    }

    async loadCartSummary() {
        try {
            const response = await fetch('/boutique/api/panier/');
            const data = await response.json();
            this.cartData = data;
            this.updateCartDisplay();
        } catch (error) {
            console.error('Erreur lors du chargement du panier:', error);
            // En cas d'erreur, initialiser avec des données vides
            this.cartData = {
                total_items: 0,
                final_price: 0,
                items: []
            };
            this.updateCartDisplay();
        }
    }

    async addToCart(bookId, quantity = 1) {
        try {
            const csrfToken = this.getCSRFToken();
            
            const response = await fetch(`/boutique/panier/ajouter/${bookId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken
                },
                body: `quantity=${quantity}&csrfmiddlewaretoken=${csrfToken}`
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                this.showNotification(data.message, 'success');
                // Recharger les données complètes du panier
                await this.loadCartSummary();
            } else {
                this.showNotification(data.error, 'error');
            }
        } catch (error) {
            console.error('Erreur lors de l\'ajout au panier:', error);
            this.showNotification('Une erreur est survenue', 'error');
        }
    }

    updateCartDisplay() {
        if (!this.cartData) return;

        const cartCount = document.getElementById('cart-count');
        const cartItems = document.getElementById('cart-items');
        const cartSummary = document.getElementById('cart-summary');
        const cartEmpty = document.getElementById('cart-empty');
        const cartTotal = document.getElementById('cart-total');

        // Mettre à jour le compteur
        if (cartCount) {
            cartCount.textContent = `Panier (${this.cartData.total_items})`;
        }

        // Mettre à jour le contenu du dropdown
        if (this.cartData.total_items > 0) {
            if (cartEmpty) cartEmpty.style.display = 'none';
            if (cartSummary) cartSummary.style.display = 'block';
            if (cartTotal) cartTotal.textContent = `${this.cartData.final_price.toFixed(2)} €`;

            // Afficher les articles (limités à 3 pour l'aperçu)
            if (cartItems) {
                cartItems.innerHTML = this.cartData.items.map(item => `
                    <div class="flex items-start mb-3 p-2 hover:bg-gray-50 rounded">
                        <a href="/boutique/livre/${item.slug || item.id}/" class="h-12 w-12 rounded overflow-hidden mr-3 flex-shrink-0 hover:opacity-80 transition-opacity">
                            ${item.cover_url ? 
                                `<img src="${item.cover_url}" alt="${item.title}" class="w-full h-full object-cover">` :
                                `<div class="w-full h-full bg-gray-200 flex items-center justify-center">
                                    <svg class="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                                    </svg>
                                </div>`
                            }
                        </a>
                        <div class="flex-1 min-w-0">
                            <a href="/boutique/livre/${item.slug || item.id}/" class="text-sm font-medium text-dark hover:text-primary truncate block" title="${item.title}">${item.title}</a>
                            <a href="/auteur/${item.author_slug || item.id}/" class="text-xs text-gray-600 hover:text-primary mb-2 block">${item.author || 'Auteur inconnu'}</a>
                            
                            <!-- Contrôles de quantité -->
                            <div class="flex items-center justify-between">
                                <div class="flex items-center space-x-1">
                                    <button onclick="window.cartManager.decreaseQuantity(${item.id})" 
                                            class="w-6 h-6 rounded-full bg-gray-200 hover:bg-gray-300 flex items-center justify-center text-xs font-bold text-gray-600">
                                        -
                                    </button>
                                    <span class="text-sm font-medium px-2">${item.quantity}</span>
                                    <button onclick="window.cartManager.increaseQuantity(${item.id})" 
                                            class="w-6 h-6 rounded-full bg-gray-200 hover:bg-gray-300 flex items-center justify-center text-xs font-bold text-gray-600">
                                        +
                                    </button>
                                </div>
                                
                                <div class="text-right">
                                    <p class="text-xs text-gray-500">
                                        ${item.is_on_sale ? 
                                            `<span class="text-red-600 font-semibold">${item.unit_price.toFixed(2)} €</span> 
                                             <span class="line-through text-gray-400">${item.original_price.toFixed(2)} €</span>` :
                                            `<span class="font-semibold">${item.unit_price.toFixed(2)} €</span>`
                                        }
                                    </p>
                                    <button onclick="window.cartManager.removeFromCart(${item.id})" 
                                            class="text-xs text-red-500 hover:text-red-700 mt-1">
                                        Supprimer
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                `).join('');
            }
        } else {
            if (cartEmpty) cartEmpty.style.display = 'block';
            if (cartSummary) cartSummary.style.display = 'none';
            if (cartItems) cartItems.innerHTML = '';
        }
    }

    showNotification(message, type = 'info') {
        // Créer une notification temporaire
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 px-6 py-3 rounded-lg text-white font-medium transition-all duration-300 ${
            type === 'success' ? 'bg-green-500' : 
            type === 'error' ? 'bg-red-500' : 
            'bg-blue-500'
        }`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Supprimer la notification après 3 secondes
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    async removeFromCart(bookId) {
        try {
            const csrfToken = this.getCSRFToken();
            
            const response = await fetch(`/boutique/panier/supprimer/${bookId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken
                },
                body: `csrfmiddlewaretoken=${csrfToken}`
            });

            const data = await response.json();

            if (data.success) {
                this.showNotification(data.message, 'success');
                // Recharger les données complètes du panier
                await this.loadCartSummary();
            } else {
                this.showNotification(data.error, 'error');
            }
        } catch (error) {
            console.error('Erreur lors de la suppression:', error);
            this.showNotification('Une erreur est survenue', 'error');
        }
    }

    async decreaseQuantity(bookId) {
        try {
            const csrfToken = this.getCSRFToken();
            
            const response = await fetch(`/boutique/panier/diminuer/${bookId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken
                },
                body: `csrfmiddlewaretoken=${csrfToken}`
            });

            const data = await response.json();

            if (data.success) {
                this.showNotification(data.message, 'success');
                // Recharger les données complètes du panier
                await this.loadCartSummary();
            } else {
                this.showNotification(data.error, 'error');
            }
        } catch (error) {
            console.error('Erreur lors de la diminution:', error);
            this.showNotification('Une erreur est survenue', 'error');
        }
    }

    async increaseQuantity(bookId) {
        // Utiliser la fonction addToCart existante pour augmenter la quantité
        await this.addToCart(bookId, 1);
    }

    async clearCart() {
        if (!confirm('Êtes-vous sûr de vouloir vider votre panier ?')) {
            return;
        }

        try {
            const csrfToken = this.getCSRFToken();
            
            const response = await fetch('/boutique/panier/vider/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken
                },
                body: `csrfmiddlewaretoken=${csrfToken}`
            });

            const data = await response.json();

            if (data.success) {
                this.showNotification(data.message, 'success');
                // Recharger les données complètes du panier
                await this.loadCartSummary();
            } else {
                this.showNotification(data.error, 'error');
            }
        } catch (error) {
            console.error('Erreur lors du vidage du panier:', error);
            this.showNotification('Une erreur est survenue', 'error');
        }
    }

    getCSRFToken() {
        // Essayer plusieurs méthodes pour récupérer le token CSRF
        let token = document.querySelector('[name=csrfmiddlewaretoken]');
        if (token) {
            return token.value;
        }
        
        // Récupérer depuis les cookies
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        
        // Récupérer depuis les meta tags
        const metaToken = document.querySelector('meta[name="csrf-token"]');
        if (metaToken) {
            return metaToken.getAttribute('content');
        }
        
        return '';
    }
}

// Initialiser le gestionnaire de panier quand le DOM est chargé
document.addEventListener('DOMContentLoaded', () => {
    window.cartManager = new CartManager();
});

// Fonctions globales pour les boutons d'ajout au panier
function addToCart(bookId, quantity = 1) {
    if (window.cartManager) {
        window.cartManager.addToCart(bookId, quantity);
    }
}
