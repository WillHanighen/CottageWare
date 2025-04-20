// Admin panel JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize any charts or data visualizations
    initializeAdminCharts();
    
    // Set up event listeners for admin actions
    setupEventListeners();
});

function initializeAdminCharts() {
    // This function would initialize any charts or data visualizations
    // using a chart library like Chart.js if it was included
    console.log('Admin charts initialized');
}

function setupEventListeners() {
    // Add event listeners for admin actions
    const deleteButtons = document.querySelectorAll('.delete-action');
    if (deleteButtons) {
        deleteButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                    e.preventDefault();
                }
            });
        });
    }
    
    // Status toggle buttons
    const toggleButtons = document.querySelectorAll('.toggle-status');
    if (toggleButtons) {
        toggleButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                const currentStatus = this.getAttribute('data-status');
                const newStatus = currentStatus === 'active' ? 'inactive' : 'active';
                const itemType = this.getAttribute('data-type');
                const message = `Are you sure you want to change this ${itemType} from ${currentStatus} to ${newStatus}?`;
                
                if (!confirm(message)) {
                    e.preventDefault();
                }
            });
        });
    }
}
