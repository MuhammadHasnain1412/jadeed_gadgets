// Recommendation system interaction tracking

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function recordInteraction(productId, interactionType) {
    // Only record if user is authenticated
    if (!window.isAuthenticated) {
        return;
    }
    
    const csrftoken = getCookie('csrftoken');
    
    fetch('/recommendations/api/record-interaction/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({
            product_id: productId,
            interaction_type: interactionType
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Interaction recorded:', interactionType, 'for product', productId);
        }
    })
    .catch(error => {
        console.error('Error recording interaction:', error);
    });
}

// Auto-record view interactions when product pages are loaded
document.addEventListener('DOMContentLoaded', function() {
    // Record product view if on product detail page
    const productId = document.querySelector('[data-product-id]');
    if (productId) {
        recordInteraction(productId.getAttribute('data-product-id'), 'view');
    }
    
    // Record interactions for add to cart buttons
    document.querySelectorAll('.add-to-cart-btn').forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.getAttribute('data-product-id');
            if (productId) {
                recordInteraction(productId, 'add_to_cart');
            }
        });
    });
    
    // Record interactions for wishlist buttons
    document.querySelectorAll('.wishlist-btn').forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.getAttribute('data-product-id');
            if (productId) {
                recordInteraction(productId, 'wishlist');
            }
        });
    });
    
    // Record interactions for purchase buttons
    document.querySelectorAll('.purchase-btn').forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.getAttribute('data-product-id');
            if (productId) {
                recordInteraction(productId, 'purchase');
            }
        });
    });
});
