// Basic form validation
document.addEventListener('DOMContentLoaded', function() {
    // Movement form validation
    const movementForm = document.querySelector('form');
    if (movementForm && movementForm.action.includes('movement')) {
        movementForm.addEventListener('submit', function(e) {
            const fromLocation = document.getElementById('from_location').value;
            const toLocation = document.getElementById('to_location').value;
            
            if (!fromLocation && !toLocation) {
                e.preventDefault();
                alert('Please select at least one location (From or To)');
                return false;
            }
        });
    }
    
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});