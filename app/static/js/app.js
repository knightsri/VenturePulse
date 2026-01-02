/**
 * VenturePulse v2 - Minimal JavaScript
 * Handles basic interactivity and form enhancements
 */

(function() {
    'use strict';

    // Auto-dismiss alerts after 5 seconds
    document.querySelectorAll('.alert').forEach(function(alert) {
        setTimeout(function() {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.3s';
            setTimeout(function() {
                alert.remove();
            }, 300);
        }, 5000);
    });

    // Form submission loading state
    document.querySelectorAll('form').forEach(function(form) {
        form.addEventListener('submit', function() {
            var submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner"></span> Processing...';
            }
        });
    });

    // Toggle visibility helper
    window.toggleVisibility = function(elementId) {
        var element = document.getElementById(elementId);
        if (element) {
            element.classList.toggle('hidden');
        }
    };

    // Confirm delete actions
    document.querySelectorAll('[data-confirm]').forEach(function(element) {
        element.addEventListener('click', function(e) {
            var message = element.getAttribute('data-confirm') || 'Are you sure?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // Copy to clipboard
    window.copyToClipboard = function(text) {
        navigator.clipboard.writeText(text).then(function() {
            // Could show a toast notification here
            console.log('Copied to clipboard');
        });
    };

    // Polling for analysis status (used on analysis progress page)
    window.pollAnalysisStatus = function(analysisId, callback, interval) {
        interval = interval || 3000;

        function poll() {
            fetch('/analysis/' + analysisId + '/status')
                .then(function(response) { return response.json(); })
                .then(function(data) {
                    callback(data);
                    if (data.status === 'running' || data.status === 'pending') {
                        setTimeout(poll, interval);
                    }
                })
                .catch(function(error) {
                    console.error('Polling error:', error);
                    setTimeout(poll, interval * 2); // Back off on error
                });
        }

        poll();
    };

})();
