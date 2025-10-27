document.addEventListener('DOMContentLoaded', function() {
    console.log('Finance Tracker loaded');
    
    // Auto-hide flash messages after 2 seconds
    const alerts = document.querySelectorAll('.alert');
    
    alerts.forEach(function(alert) {
        // Add hiding animation after 2 seconds
        setTimeout(function() {
            alert.classList.add('hiding');
            
            // Remove from DOM after animation completes
            setTimeout(function() {
                alert.remove();
            }, 300); // Wait for animation to finish
        }, 2000); // Show for 2 seconds
    });
});
