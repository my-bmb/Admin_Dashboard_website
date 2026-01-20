// Admin Dashboard JavaScript

$(document).ready(function() {
    // Initialize DataTables
    $('.datatable').DataTable({
        pageLength: 25,
        responsive: true,
        order: [[0, 'desc']],
        language: {
            search: "_INPUT_",
            searchPlaceholder: "Search...",
            lengthMenu: "_MENU_ records per page",
            zeroRecords: "No records found",
            info: "Showing _START_ to _END_ of _TOTAL_ records",
            infoEmpty: "No records available",
            infoFiltered: "(filtered from _MAX_ total records)"
        }
    });
    
    // Auto-refresh data tables every 30 seconds
    setInterval(function() {
        $('.datatable').DataTable().ajax.reload(null, false);
    }, 30000);
    
    // Confirm delete actions
    $('.confirm-delete').on('click', function(e) {
        e.preventDefault();
        const url = $(this).attr('href');
        const itemName = $(this).data('name') || 'this item';
        
        if (confirm(`Are you sure you want to delete ${itemName}? This action cannot be undone.`)) {
            window.location.href = url;
        }
    });
    
    // Update order status
    $('.update-status').on('change', function() {
        const orderId = $(this).data('order-id');
        const newStatus = $(this).val();
        const url = `/dashboard/orders/${orderId}/update-status`;
        
        // Show loading
        const originalText = $(this).parent().find('.status-text');
        const originalStatus = originalText.text();
        originalText.html('<span class="spinner-border spinner-border-sm"></span> Updating...');
        
        $.ajax({
            url: url,
            type: 'POST',
            data: {
                status: newStatus
            },
            success: function(response) {
                if (response.success) {
                    // Update UI
                    originalText.text(response.new_status.toUpperCase());
                    
                    // Update status badge
                    const badge = $(`#status-badge-${orderId}`);
                    badge.removeClass('bg-primary bg-warning bg-info bg-success bg-danger');
                    
                    let badgeClass = 'bg-secondary';
                    if (response.new_status === 'pending') badgeClass = 'bg-primary';
                    else if (response.new_status === 'processing') badgeClass = 'bg-warning';
                    else if (response.new_status === 'confirmed') badgeClass = 'bg-info';
                    else if (response.new_status === 'delivered') badgeClass = 'bg-success';
                    else if (response.new_status === 'cancelled') badgeClass = 'bg-danger';
                    
                    badge.addClass(badgeClass).text(response.new_status.toUpperCase());
                    
                    // Show success message
                    showToast('Success', 'Order status updated successfully', 'success');
                } else {
                    showToast('Error', response.message, 'danger');
                    // Reset select
                    $(this).val($(this).data('original-status'));
                }
            },
            error: function(xhr, status, error) {
                showToast('Error', 'Failed to update status: ' + error, 'danger');
                // Reset select
                $(this).val($(this).data('original-status'));
                originalText.text(originalStatus);
            }
        });
    });
    
    // Toggle user active status
    $('.toggle-active').on('change', function() {
        const userId = $(this).data('user-id');
        const isActive = $(this).is(':checked');
        const url = `/dashboard/users/${userId}/toggle-active`;
        
        $.ajax({
            url: url,
            type: 'POST',
            success: function(response) {
                if (response.success) {
                    const statusText = isActive ? 'activated' : 'deactivated';
                    showToast('Success', `User ${statusText} successfully`, 'success');
                    
                    // Update status badge
                    const badge = $(`#user-status-${userId}`);
                    badge.removeClass('bg-success bg-danger');
                    badge.addClass(isActive ? 'bg-success' : 'bg-danger');
                    badge.text(isActive ? 'Active' : 'Inactive');
                } else {
                    showToast('Error', response.message, 'danger');
                    // Toggle back
                    $(this).prop('checked', !isActive);
                }
            },
            error: function(xhr, status, error) {
                showToast('Error', 'Failed to update user status: ' + error, 'danger');
                // Toggle back
                $(this).prop('checked', !isActive);
            }
        });
    });
    
    // Toggle review approval
    $('.toggle-approval').on('change', function() {
        const reviewId = $(this).data('review-id');
        const isApproved = $(this).is(':checked');
        const url = `/dashboard/reviews/${reviewId}/toggle-approval`;
        
        $.ajax({
            url: url,
            type: 'POST',
            success: function(response) {
                if (response.success) {
                    const statusText = isApproved ? 'approved' : 'unapproved';
                    showToast('Success', `Review ${statusText} successfully`, 'success');
                    
                    // Update approval badge
                    const badge = $(`#review-status-${reviewId}`);
                    badge.removeClass('bg-success bg-warning');
                    badge.addClass(isApproved ? 'bg-success' : 'bg-warning');
                    badge.text(isApproved ? 'Approved' : 'Pending');
                } else {
                    showToast('Error', response.message, 'danger');
                    // Toggle back
                    $(this).prop('checked', !isApproved);
                }
            },
            error: function(xhr, status, error) {
                showToast('Error', 'Failed to update review: ' + error, 'danger');
                // Toggle back
                $(this).prop('checked', !isApproved);
            }
        });
    });
    
    // Image preview for file inputs
    $('.image-preview').on('change', function(e) {
        const input = this;
        const preview = $(this).data('preview');
        
        if (input.files && input.files[0]) {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                $(preview).attr('src', e.target.result).show();
            }
            
            reader.readAsDataURL(input.files[0]);
        }
    });
    
    // Cloudinary upload progress
    $('.cloudinary-upload').on('submit', function(e) {
        const form = $(this);
        const submitBtn = form.find('button[type="submit"]');
        const originalText = submitBtn.html();
        
        submitBtn.prop('disabled', true);
        submitBtn.html('<span class="spinner-border spinner-border-sm"></span> Uploading...');
        
        // You can add Cloudinary upload progress here
    });
    
    // Real-time updates for dashboard
    function updateDashboardStats() {
        $.ajax({
            url: '/api/dashboard/stats?period=today',
            type: 'GET',
            success: function(response) {
                if (response.success) {
                    // Update stats in real-time
                    updateStatsDisplay(response.stats);
                }
            }
        });
    }
    
    // Update stats display
    function updateStatsDisplay(stats) {
        $('[data-stat="orders"]').text(stats.order_count);
        $('[data-stat="revenue"]').text('₹' + stats.revenue.toLocaleString('en-IN'));
        $('[data-stat="avg-order"]').text('₹' + stats.avg_order_value.toFixed(2));
        $('[data-stat="customers"]').text(stats.new_customers);
    }
    
    // Initialize real-time updates every 60 seconds
    setInterval(updateDashboardStats, 60000);
    
    // Toast notification function
    function showToast(title, message, type = 'info') {
        // Create toast container if it doesn't exist
        if (!$('#toastContainer').length) {
            $('body').append(`
                <div id="toastContainer" class="toast-container position-fixed top-0 end-0 p-3" style="z-index: 9999">
                </div>
            `);
        }
        
        const toastId = 'toast-' + Date.now();
        const toastHtml = `
            <div id="${toastId}" class="toast align-items-center text-bg-${type} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        <strong>${title}</strong><br>
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        $('#toastContainer').append(toastHtml);
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
        
        // Remove toast after it hides
        toastElement.addEventListener('hidden.bs.toast', function() {
            $(this).remove();
        });
    }
    
    // Export data functionality
    $('.export-data').on('click', function(e) {
        e.preventDefault();
        const exportType = $(this).data('type');
        const url = $(this).data('url');
        
        // Show loading
        showToast('Info', 'Preparing export...', 'info');
        
        $.ajax({
            url: url,
            type: 'GET',
            data: { format: 'csv' },
            xhrFields: {
                responseType: 'blob'
            },
            success: function(data) {
                const blob = new Blob([data], { type: 'text/csv' });
                const link = document.createElement('a');
                link.href = window.URL.createObjectURL(blob);
                link.download = `export_${exportType}_${new Date().toISOString().slice(0, 10)}.csv`;
                link.click();
                
                showToast('Success', 'Export completed successfully', 'success');
            },
            error: function(xhr, status, error) {
                showToast('Error', 'Export failed: ' + error, 'danger');
            }
        });
    });
    
    // Bulk actions
    $('.bulk-action').on('click', function() {
        const action = $(this).data('action');
        const selectedIds = [];
        
        $('.bulk-select:checked').each(function() {
            selectedIds.push($(this).val());
        });
        
        if (selectedIds.length === 0) {
            showToast('Warning', 'Please select items to perform this action', 'warning');
            return;
        }
        
        if (confirm(`Are you sure you want to ${action} ${selectedIds.length} selected item(s)?`)) {
            // Implement bulk action
            console.log(`Bulk ${action} for IDs:`, selectedIds);
        }
    });
    
    // Select all checkbox
    $('.select-all').on('change', function() {
        const isChecked = $(this).is(':checked');
        $('.bulk-select').prop('checked', isChecked);
    });
    
    // Print functionality
    $('.print-page').on('click', function() {
        window.print();
    });
    
    // Theme switcher (if implemented)
    $('.theme-switcher').on('click', function() {
        const currentTheme = $('html').attr('data-bs-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        $('html').attr('data-bs-theme', newTheme);
        
        // Save preference to localStorage
        localStorage.setItem('theme', newTheme);
        
        showToast('Theme Changed', `Switched to ${newTheme} mode`, 'info');
    });
    
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        $('html').attr('data-bs-theme', savedTheme);
    }
    
    // Initialize tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    
    // Initialize popovers
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
    const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
});

// Global functions
function formatCurrency(amount) {
    return '₹' + parseFloat(amount).toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function getTimeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    if (seconds < 60) return 'just now';
    
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    
    const days = Math.floor(hours / 24);
    if (days < 30) return `${days}d ago`;
    
    const months = Math.floor(days / 30);
    if (months < 12) return `${months}mo ago`;
    
    const years = Math.floor(months / 12);
    return `${years}y ago`;
}