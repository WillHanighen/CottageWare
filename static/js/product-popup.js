// Product Popup Functionality
document.addEventListener('DOMContentLoaded', function() {
    // Create popup elements
    const popupOverlay = document.createElement('div');
    popupOverlay.className = 'product-popup-overlay';
    
    const popupContent = document.createElement('div');
    popupContent.className = 'product-popup-content';
    
    // Popup structure
    popupContent.innerHTML = `
        <div class="product-popup-header">
            <h2 class="product-popup-title"></h2>
            <button class="product-popup-close">&times;</button>
        </div>
        <div class="product-popup-body">
            <div class="product-popup-image">
                <div class="product-popup-image-content"></div>
                <div class="product-popup-action-row">
                    <div class="product-popup-price"></div>
                    <div class="product-popup-actions"></div>
                </div>
            </div>
            <div class="product-popup-details">
                <div class="product-popup-description"></div>
            </div>
        </div>
    `;
    
    popupOverlay.appendChild(popupContent);
    document.body.appendChild(popupOverlay);
    
    // Close popup when clicking the close button
    const closeButton = popupContent.querySelector('.product-popup-close');
    closeButton.addEventListener('click', closePopup);
    
    // Close popup when clicking outside the content
    popupOverlay.addEventListener('click', function(e) {
        if (e.target === popupOverlay) {
            closePopup();
        }
    });
    
    // Close popup with Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && popupOverlay.classList.contains('active')) {
            closePopup();
        }
    });
    
    // Add click event to all product cards
    const productCards = document.querySelectorAll('.product-card');
    productCards.forEach(card => {
        card.style.cursor = 'pointer';
        card.addEventListener('click', function(e) {
            // Don't open popup if clicking on the purchase button
            if (e.target.closest('.sellapp-button-container') || e.target.closest('button')) {
                return;
            }
            
            openProductPopup(card);
        });
    });
    
    function openProductPopup(productCard) {
        // Get product data
        const title = productCard.querySelector('.product-title').textContent;
        const fullDescriptionElement = productCard.querySelector('.product-full-description');
        const description = fullDescriptionElement && fullDescriptionElement.innerHTML ? 
                           fullDescriptionElement.innerHTML : 
                           productCard.querySelector('.product-description').innerHTML;
        const priceElement = productCard.querySelector('.product-price').cloneNode(true);
        
        // Get image
        let imageContent = '';
        const productImage = productCard.querySelector('.product-image');
        if (productImage.querySelector('img')) {
            const img = productImage.querySelector('img').cloneNode(true);
            imageContent = document.createElement('div');
            imageContent.appendChild(img);
            imageContent = imageContent.innerHTML;
        } else {
            const placeholder = productImage.querySelector('.product-image-placeholder');
            if (placeholder) {
                imageContent = `
                    <div class="product-popup-image-placeholder">
                        <i class="fas fa-gamepad"></i>
                    </div>
                `;
            }
        }
        
        // Get purchase button
        const purchaseButton = productCard.querySelector('.sellapp-button-container button');
        
        // Set popup content
        const popupContent = document.querySelector('.product-popup-content');
        popupContent.querySelector('.product-popup-title').textContent = title;
        popupContent.querySelector('.product-popup-image-content').innerHTML = imageContent;
        popupContent.querySelector('.product-popup-description').innerHTML = description;
        popupContent.querySelector('.product-popup-price').innerHTML = priceElement.innerHTML;
        
        // Add TOS checkbox and purchase button
        const actionsContainer = popupContent.querySelector('.product-popup-actions');
        actionsContainer.innerHTML = `
            <div class="tos-checkbox-container">
                <label class="tos-checkbox-label">
                    <input type="checkbox" id="tos-checkbox" class="tos-checkbox">
                    I have read and accept the <a href="/terms_of_service" target="_blank">Terms of Service</a> and <a href="/privacy_policy" target="_blank">Privacy Policy</a>
                </label>
            </div>
            ${purchaseButton.outerHTML}
        `;
        
        // Get the newly added elements
        const tosCheckbox = actionsContainer.querySelector('#tos-checkbox');
        const popupPurchaseButton = actionsContainer.querySelector('button');
        
        // Disable the purchase button initially
        popupPurchaseButton.disabled = true;
        popupPurchaseButton.style.opacity = '0.5';
        popupPurchaseButton.style.cursor = 'not-allowed';
        
        // Enable/disable purchase button based on checkbox
        tosCheckbox.addEventListener('change', function() {
            popupPurchaseButton.disabled = !this.checked;
            popupPurchaseButton.style.opacity = this.checked ? '1' : '0.5';
            popupPurchaseButton.style.cursor = this.checked ? 'pointer' : 'not-allowed';
        });
        
        // Initialize Sell.app button in the popup
        if (window.SellApp && typeof window.SellApp.init === 'function') {
            setTimeout(() => {
                window.SellApp.init();
            }, 100);
        }
        
        // Show popup
        popupOverlay.classList.add('active');
        document.body.classList.add('popup-open');
    }
    
    function closePopup() {
        popupOverlay.classList.remove('active');
        document.body.classList.remove('popup-open');
    }
});
