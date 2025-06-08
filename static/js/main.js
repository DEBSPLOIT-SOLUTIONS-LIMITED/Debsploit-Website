// Debsploit Solutions - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeNavigation();
    initializeScrollEffects();
    initializeAnimations();
    initializeForms();
    initializeModals();
    initializeTooltips();
    initializeNotifications();
    
    // Development mode logging
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        console.log('🚀 Debsploit Solutions - Development Mode');
    }
});

// Navigation functionality
function initializeNavigation() {
    const navbar = document.getElementById('mainNavbar');
    const mobileToggle = document.querySelector('.navbar-toggler');
    const navMenu = document.querySelector('.navbar-collapse');
    
    // Navbar scroll effect
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });
    
    // Mobile menu close on link click
    if (navMenu) {
        navMenu.addEventListener('click', (e) => {
            if (e.target.classList.contains('nav-link')) {
                const bsCollapse = new bootstrap.Collapse(navMenu);
                bsCollapse.hide();
            }
        });
    }
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                const offsetTop = target.offsetTop - (navbar ? navbar.offsetHeight : 0);
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Active navigation highlighting
    const navLinks = document.querySelectorAll('.nav-link');
    const currentPath = window.location.pathname;
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
}

// Scroll effects
function initializeScrollEffects() {
    // Back to top button
    const backToTopBtn = document.getElementById('backToTop');
    if (backToTopBtn) {
        window.addEventListener('scroll', () => {
            if (window.pageYOffset > 300) {
                backToTopBtn.classList.remove('d-none');
            } else {
                backToTopBtn.classList.add('d-none');
            }
        });
        
        backToTopBtn.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }
    
    // Parallax effect for hero sections
    const heroSections = document.querySelectorAll('.hero, .hero-section');
    if (heroSections.length > 0) {
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            heroSections.forEach(hero => {
                const rate = scrolled * -0.5;
                hero.style.transform = `translateY(${rate}px)`;
            });
        });
    }
    
    // Reveal animations on scroll
    const revealElements = document.querySelectorAll('[data-reveal]');
    if (revealElements.length > 0) {
        const revealObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('revealed');
                    revealObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });
        
        revealElements.forEach(el => {
            el.classList.add('reveal-hidden');
            revealObserver.observe(el);
        });
    }
}

// Animation initialization
function initializeAnimations() {
    // Counter animations
    const counters = document.querySelectorAll('[data-counter]');
    if (counters.length > 0) {
        const counterObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateCounter(entry.target);
                    counterObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });
        
        counters.forEach(counter => {
            counterObserver.observe(counter);
        });
    }
    
    // Progress bar animations
    const progressBars = document.querySelectorAll('.progress-bar[data-width]');
    if (progressBars.length > 0) {
        const progressObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const bar = entry.target;
                    const width = bar.getAttribute('data-width');
                    setTimeout(() => {
                        bar.style.width = width + '%';
                    }, 200);
                    progressObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });
        
        progressBars.forEach(bar => {
            bar.style.width = '0%';
            progressObserver.observe(bar);
        });
    }
    
    // Typing animation
    const typingElements = document.querySelectorAll('[data-typing]');
    typingElements.forEach(element => {
        const text = element.textContent;
        element.textContent = '';
        typeText(element, text, 50);
    });
}

// Form enhancements
function initializeForms() {
    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
    
    // Auto-resize textareas
    const textareas = document.querySelectorAll('textarea[data-auto-resize]');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
    });
    
    // Newsletter form
    const newsletterForm = document.getElementById('newsletter-form');
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', handleNewsletterSubmit);
    }
    
    // Contact form enhancements
    const contactForms = document.querySelectorAll('[data-contact-form]');
    contactForms.forEach(form => {
        form.addEventListener('submit', handleContactFormSubmit);
    });
    
    // File upload preview
    const fileInputs = document.querySelectorAll('input[type="file"][data-preview]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const file = this.files[0];
            const previewContainer = document.querySelector(this.dataset.preview);
            
            if (file && previewContainer) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    if (file.type.startsWith('image/')) {
                        previewContainer.innerHTML = `<img src="${e.target.result}" class="img-fluid rounded" alt="Preview">`;
                    } else {
                        previewContainer.innerHTML = `<div class="alert alert-info"><i class="fas fa-file me-2"></i>${file.name}</div>`;
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    });
}

// Modal functionality
function initializeModals() {
    // Auto-focus first input in modals
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('shown.bs.modal', function() {
            const firstInput = this.querySelector('input:not([type="hidden"]):not([readonly]), textarea:not([readonly]), select:not([readonly])');
            if (firstInput) {
                firstInput.focus();
            }
        });
        
        // Reset forms when modal is hidden
        modal.addEventListener('hidden.bs.modal', function() {
            const forms = this.querySelectorAll('form');
            forms.forEach(form => {
                form.reset();
                form.classList.remove('was-validated');
            });
        });
    });
    
    // Confirmation modals
    document.addEventListener('click', function(e) {
        if (e.target.matches('[data-confirm]')) {
            e.preventDefault();
            const message = e.target.dataset.confirm;
            const action = e.target.href || e.target.dataset.action;
            
            showConfirmModal(message, action);
        }
    });
}

// Tooltip and popover initialization
function initializeTooltips() {
    // Initialize Bootstrap tooltips
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(tooltip => {
        new bootstrap.Tooltip(tooltip);
    });
    
    // Initialize Bootstrap popovers
    const popovers = document.querySelectorAll('[data-bs-toggle="popover"]');
    popovers.forEach(popover => {
        new bootstrap.Popover(popover);
    });
}

// Notification system
function initializeNotifications() {
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Notification permission request
    if ('Notification' in window && Notification.permission === 'default') {
        setTimeout(() => {
            if (confirm('Would you like to receive notifications from Debsploit Solutions?')) {
                Notification.requestPermission();
            }
        }, 3000);
    }
}

// Utility functions
function animateCounter(element) {
    const target = parseInt(element.textContent);
    const duration = 2000;
    const increment = target / (duration / 16);
    let current = 0;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            element.textContent = target;
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(current);
        }
    }, 16);
}

function typeText(element, text, speed = 100) {
    let i = 0;
    const timer = setInterval(() => {
        element.textContent += text.charAt(i);
        i++;
        if (i >= text.length) {
            clearInterval(timer);
        }
    }, speed);
}

function showConfirmModal(message, action) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Confirmation</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p>${message}</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-primary" id="confirmAction">Confirm</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    document.getElementById('confirmAction').addEventListener('click', () => {
        window.location.href = action;
    });
    
    modal.addEventListener('hidden.bs.modal', () => {
        modal.remove();
    });
}

// Form handlers
function handleNewsletterSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const email = form.querySelector('input[type="email"]').value;
    const button = form.querySelector('button[type="submit"]');
    const originalText = button.innerHTML;
    
    // Show loading state
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Subscribing...';
    button.disabled = true;
    
    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                     document.querySelector('meta[name="csrf-token"]')?.content;
    
    fetch('/api/newsletter-signup/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ email: email })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Success!', data.message, 'success');
            form.reset();
        } else {
            showToast('Error!', data.message, 'error');
        }
    })
    .catch(error => {
        showToast('Error!', 'Failed to subscribe. Please try again.', 'error');
        console.error('Newsletter signup error:', error);
    })
    .finally(() => {
        button.innerHTML = originalText;
        button.disabled = false;
    });
}

function handleContactFormSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);
    const button = form.querySelector('button[type="submit"]');
    const originalText = button.innerHTML;
    
    // Show loading state
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Sending...';
    button.disabled = true;
    
    fetch(form.action || '/contact/', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.ok) {
            showToast('Success!', 'Message sent successfully!', 'success');
            form.reset();
        } else {
            throw new Error('Failed to send message');
        }
    })
    .catch(error => {
        showToast('Error!', 'Failed to send message. Please try again.', 'error');
        console.error('Contact form error:', error);
    })
    .finally(() => {
        button.innerHTML = originalText;
        button.disabled = false;
    });
}

// Toast notification system
function showToast(title, message, type = 'info') {
    const toastContainer = getOrCreateToastContainer();
    const toastId = 'toast-' + Date.now();
    
    const typeClasses = {
        success: 'text-bg-success',
        error: 'text-bg-danger',
        warning: 'text-bg-warning',
        info: 'text-bg-primary'
    };
    
    const toastHTML = `
        <div class="toast ${typeClasses[type] || typeClasses.info}" role="alert" id="${toastId}">
            <div class="d-flex">
                <div class="toast-body">
                    <strong>${title}</strong><br>${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { autohide: true, delay: 5000 });
    
    toast.show();
    
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

function getOrCreateToastContainer() {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1055';
        document.body.appendChild(container);
    }
    return container;
}

// AJAX utilities
function makeRequest(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    };
    
    // Add CSRF token for POST requests
    if (options.method === 'POST' || options.method === 'PUT' || options.method === 'DELETE') {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                         document.querySelector('meta[name="csrf-token"]')?.content;
        if (csrfToken) {
            defaultOptions.headers['X-CSRFToken'] = csrfToken;
        }
    }
    
    const finalOptions = { ...defaultOptions, ...options };
    
    return fetch(url, finalOptions)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .catch(error => {
            console.error('Request failed:', error);
            throw error;
        });
}

// Dashboard specific functions
if (window.location.pathname.startsWith('/dashboard/')) {
    document.addEventListener('DOMContentLoaded', function() {
        initializeDashboard();
    });
}

function initializeDashboard() {
    // Auto-refresh dashboard data every 60 seconds
    setInterval(refreshDashboardData, 60000);
    
    // Initialize progress tracking
    initializeProgressTracking();
    
    // Initialize task management
    initializeTaskManagement();
    
    // Initialize notification handling
    initializeDashboardNotifications();
}

function refreshDashboardData() {
    // Update user points
    fetch('/dashboard/api/user-stats/')
        .then(response => response.json())
        .then(data => {
            const pointsElement = document.querySelector('[data-user-points]');
            if (pointsElement && data.points !== undefined) {
                pointsElement.textContent = data.points;
            }
        })
        .catch(error => console.log('Error refreshing dashboard data:', error));
}

function initializeProgressTracking() {
    const progressSliders = document.querySelectorAll('[data-skill-progress]');
    
    progressSliders.forEach(slider => {
        slider.addEventListener('change', function() {
            const skillArea = this.dataset.skillProgress;
            const progressValue = this.value;
            
            updateUserProgress(skillArea, progressValue);
        });
    });
}

function updateUserProgress(skillArea, progressValue) {
    makeRequest('/dashboard/api/progress/update/', {
        method: 'POST',
        body: JSON.stringify({
            skill_area: skillArea,
            progress: progressValue
        })
    })
    .then(data => {
        if (data.success) {
            showToast('Progress Updated!', `${skillArea} progress updated to ${progressValue}%`, 'success');
        } else {
            showToast('Error!', data.error || 'Failed to update progress', 'error');
        }
    })
    .catch(error => {
        showToast('Error!', 'Failed to update progress', 'error');
    });
}

function initializeTaskManagement() {
    // Task application handling
    const taskApplicationForms = document.querySelectorAll('[data-task-application]');
    taskApplicationForms.forEach(form => {
        form.addEventListener('submit', handleTaskApplication);
    });
    
    // Task status updates
    const taskStatusButtons = document.querySelectorAll('[data-task-status]');
    taskStatusButtons.forEach(button => {
        button.addEventListener('click', handleTaskStatusUpdate);
    });
    
    // Task filtering
    const taskFilters = document.querySelectorAll('[data-task-filter]');
    taskFilters.forEach(filter => {
        filter.addEventListener('change', handleTaskFilter);
    });
}

function handleTaskApplication(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);
    const submitButton = form.querySelector('button[type="submit"]');
    
    submitButton.disabled = true;
    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Applying...';
    
    fetch(form.action, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.ok) {
            showToast('Success!', 'Application submitted successfully!', 'success');
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        } else {
            throw new Error('Failed to submit application');
        }
    })
    .catch(error => {
        showToast('Error!', 'Failed to submit application', 'error');
        submitButton.disabled = false;
        submitButton.innerHTML = 'Submit Application';
    });
}

function handleTaskStatusUpdate(e) {
    const button = e.target;
    const taskId = button.dataset.taskId;
    const newStatus = button.dataset.taskStatus;
    
    makeRequest(`/dashboard/api/tasks/${taskId}/status/`, {
        method: 'POST',
        body: JSON.stringify({ status: newStatus })
    })
    .then(data => {
        if (data.success) {
            showToast('Success!', 'Task status updated!', 'success');
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showToast('Error!', data.error || 'Failed to update task status', 'error');
        }
    })
    .catch(error => {
        showToast('Error!', 'Failed to update task status', 'error');
    });
}

function handleTaskFilter(e) {
    const filter = e.target;
    const filterValue = filter.value;
    const currentUrl = new URL(window.location);
    
    if (filterValue) {
        currentUrl.searchParams.set('filter', filterValue);
    } else {
        currentUrl.searchParams.delete('filter');
    }
    
    window.location.href = currentUrl.toString();
}

function initializeDashboardNotifications() {
    // Mark notification as read when clicked
    document.addEventListener('click', function(e) {
        if (e.target.closest('[data-notification-id]')) {
            const notificationElement = e.target.closest('[data-notification-id]');
            const notificationId = notificationElement.dataset.notificationId;
            
            if (!notificationElement.classList.contains('read')) {
                markNotificationAsRead(notificationId);
                notificationElement.classList.add('read');
            }
        }
    });
    
    // Mark all notifications as read
    const markAllReadButton = document.querySelector('[data-mark-all-read]');
    if (markAllReadButton) {
        markAllReadButton.addEventListener('click', function() {
            markAllNotificationsAsRead();
        });
    }
}

function markNotificationAsRead(notificationId) {
    makeRequest(`/dashboard/api/notifications/${notificationId}/read/`, {
        method: 'POST'
    })
    .then(data => {
        if (data.success) {
            updateNotificationCount();
        }
    })
    .catch(error => {
        console.log('Error marking notification as read:', error);
    });
}

function markAllNotificationsAsRead() {
    makeRequest('/dashboard/api/notifications/read-all/', {
        method: 'POST'
    })
    .then(data => {
        if (data.success) {
            showToast('Success!', 'All notifications marked as read', 'success');
            updateNotificationCount();
            
            // Update UI
            document.querySelectorAll('[data-notification-id]').forEach(el => {
                el.classList.add('read');
            });
        }
    })
    .catch(error => {
        showToast('Error!', 'Failed to mark notifications as read', 'error');
    });
}

function updateNotificationCount() {
    const badge = document.querySelector('.notification-badge');
    if (badge) {
        const currentCount = parseInt(badge.textContent) || 0;
        const newCount = Math.max(0, currentCount - 1);
        
        if (newCount === 0) {
            badge.style.display = 'none';
        } else {
            badge.textContent = newCount;
        }
    }
}

// File upload utilities
function handleFileUpload(input, callback) {
    const file = input.files[0];
    if (!file) return;
    
    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
        showToast('Error!', 'File size must be less than 10MB', 'error');
        return;
    }
    
    // Validate file type
    const allowedTypes = input.accept ? input.accept.split(',').map(type => type.trim()) : [];
    if (allowedTypes.length > 0 && !allowedTypes.some(type => file.type.match(type))) {
        showToast('Error!', 'Invalid file type', 'error');
        return;
    }
    
    if (callback) {
        callback(file);
    }
}

// Search functionality
function initializeSearch() {
    const searchInput = document.querySelector('[data-search]');
    if (searchInput) {
        let searchTimeout;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performSearch(this.value);
            }, 300);
        });
    }
}

function performSearch(query) {
    if (query.length < 2) return;
    
    makeRequest(`/api/search/?q=${encodeURIComponent(query)}`)
        .then(data => {
            displaySearchResults(data.results);
        })
        .catch(error => {
            console.log('Search error:', error);
        });
}

function displaySearchResults(results) {
    const searchResults = document.querySelector('[data-search-results]');
    if (!searchResults) return;
    
    if (results.length === 0) {
        searchResults.innerHTML = '<div class="text-muted p-3">No results found</div>';
        return;
    }
    
    const resultHTML = results.map(result => `
        <div class="search-result-item p-3 border-bottom">
            <h6><a href="${result.url}" class="text-decoration-none">${result.title}</a></h6>
            <p class="text-muted small mb-1">${result.description}</p>
            <span class="badge bg-secondary">${result.type}</span>
        </div>
    `).join('');
    
    searchResults.innerHTML = resultHTML;
}

// Performance monitoring
function trackPerformance() {
    if ('performance' in window) {
        window.addEventListener('load', () => {
            setTimeout(() => {
                const perfData = performance.getEntriesByType('navigation')[0];
                const loadTime = perfData.loadEventEnd - perfData.loadEventStart;
                
                // Send performance data to analytics (if configured)
                if (window.gtag) {
                    gtag('event', 'page_load_time', {
                        custom_parameter: loadTime
                    });
                }
                
                console.log(`Page load time: ${loadTime}ms`);
            }, 0);
        });
    }
}

// Error handling
window.addEventListener('error', function(e) {
    console.error('JavaScript Error:', e.error);
    
    // Send error to analytics (if configured)
    if (window.gtag) {
        gtag('event', 'exception', {
            description: e.error.message,
            fatal: false
        });
    }
});

// Initialize performance tracking
trackPerformance();

// Export functions for global use
window.DebsploitUtils = {
    showToast,
    makeRequest,
    updateUserProgress,
    markNotificationAsRead,
    markAllNotificationsAsRead,
    handleFileUpload
};