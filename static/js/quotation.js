/**
 * Arihant Agro Services - Quotation JavaScript
 * Handles quotation calculations and form interactions
 */

// Product data storage
let productData = window.productsData || {};
let isAdmin = false; // Will be set from HTML data attribute

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    // Get admin status from body data attribute
    isAdmin = document.body.dataset.isAdmin === 'true';
    const brandSelect = document.getElementById("brandSelect");
    const kitSelect = document.getElementById("kitSelect");

    if (brandSelect) {
        brandSelect.addEventListener("change", function () {

            const brandId = this.value;

            if (!brandId) return;

            fetch(`/api/get-kits-by-brand/${brandId}`)
                .then(res => res.json())
                .then(kits => {

                    kitSelect.innerHTML = '<option value="">संच निवडा</option>';

                    kits.forEach(kit => {

                        const option = document.createElement("option");

                        option.value = kit._id;
                        option.textContent = kit.name;

                        kitSelect.appendChild(option);

                    });

                })
                .catch(err => console.log(err));

        });
    }
    // Initialize tooltips
    initializeTooltips();

    // Initialize mobile menu
    initializeMobileMenu();

    // Initialize flash messages auto-dismiss
    initializeFlashMessages();

    // Initialize smooth scroll
    initializeSmoothScroll();

    // Initialize quotation form if present
    initializeQuotationForm();

    // Initialize kit select if present
    initializeKitSelect();
});

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    if (tooltipTriggerList.length > 0 && typeof bootstrap !== 'undefined') {
        tooltipTriggerList.forEach(function (tooltipTriggerEl) {
            new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

/**
 * Initialize mobile menu
 */
function initializeMobileMenu() {
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');

    if (navbarToggler && navbarCollapse) {
        navbarToggler.addEventListener('click', function () {
            navbarCollapse.classList.toggle('show');
        });

        // Close menu when clicking outside
        document.addEventListener('click', function (e) {
            if (!navbarToggler.contains(e.target) && !navbarCollapse.contains(e.target)) {
                navbarCollapse.classList.remove('show');
            }
        });
    }
}

/**
 * Initialize flash messages auto-dismiss
 */
function initializeFlashMessages() {
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        // Auto dismiss after 5 seconds
        setTimeout(function () {
            const closeButton = alert.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            }
        }, 5000);
    });
}

/**
 * Initialize smooth scroll for anchor links
 */
function initializeSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href');
            if (targetId !== '#') {
                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    e.preventDefault();
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
}

/**
 * Initialize quotation form functionality
 */
function initializeQuotationForm() {
    const quotationForm = document.getElementById('quotationForm');
    if (!quotationForm) return;

    // Initialize product data from select elements
    initializeProductData();

    // Add item button
    const addItemBtn = document.getElementById('addItemBtn');
    if (addItemBtn) {
        addItemBtn.addEventListener('click', addNewItemRow);
    }

    // Discount input
    const discountInput = document.getElementById('discountInput');
    if (discountInput) {
        discountInput.addEventListener('input', calculateTotals);
    }

    // Initialize product selects
    initializeProductSelects();

    // Initial calculation
    calculateTotals();

    // Form validation
    quotationForm.addEventListener('submit', validateQuotationForm);
}

/**
 * Initialize kit select functionality
 */
function initializeKitSelect() {
    const kitSelect = document.getElementById("kitSelect");
    if (kitSelect) {
        kitSelect.addEventListener("change", function () {
            const kitId = this.value;
            if (!kitId) return;

            fetch(`/api/get-kit/${kitId}`)
                .then(res => {
                    if (!res.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return res.json();
                })
                .then(data => {
                    loadKitItems(data);
                })
                .catch(error => {
                    console.error('Error loading kit:', error);
                    showNotification('किट लोड करताना त्रुटी आली', 'error');
                });
        });
    }
}

/**
 * Load kit items into the form
 */
function loadKitItems(data) {
    const container = document.getElementById('itemsContainer');
    if (!container) return;

    container.innerHTML = "";

    if (data.items && data.items.length > 0) {
        data.items.forEach(item => {
            const row = document.createElement('div');
            row.className = 'item-row border rounded p-3 mb-3';

            // Get rate field HTML based on admin status
            const rateFieldHTML = getRateFieldHTML(item.rate);

            row.innerHTML = `
                <div class="row align-items-end">
                    <div class="col-md-4 mb-3">
                        <label class="form-label">उत्पादन *</label>
                        <select class="form-select product-select" name="product_id[]" required onchange="updateProductInfo(this)">
                            <option value="">उत्पादन निवडा</option>
                            <option value="${item.product_id}" data-rate="${item.rate}" data-cml="${item.cml_no || ''}" selected>${item.product_name}</option>
                        </select>
                    </div>
                    <div class="col-md-2 mb-3">
                        <label class="form-label">CML नं.</label>
                        <input type="text" class="form-control cml-input" value="${item.cml_no || ''}" readonly>
                    </div>
                    <div class="col-md-2 mb-3">
                        <label class="form-label">साईझ</label>
                        <input type="text" class="form-control" name="size[]" value="${data.size || ''}">
                    </div>
                    <div class="col-md-2 mb-3">
                        <label class="form-label">प्रमाण *</label>
                        <input type="number" class="form-control quantity-input" name="quantity[]" value="${item.quantity}" min="1" required onchange="calculateTotals()">
                    </div>
                    <div class="col-md-2 mb-3">
                        <label class="form-label">दर (₹)</label>
                        ${rateFieldHTML}
                    </div>
                </div>
                <div class="row">
                    <div class="col-12 text-end">
                        <button type="button" class="btn btn-danger btn-sm remove-item" onclick="removeItemRow(this)">
                            <i class="fas fa-trash"></i> काढून टाका
                        </button>
                    </div>
                </div>
            `;
            container.appendChild(row);
        });

        // Calculate totals after loading kit items
        calculateTotals();
    } else {
        showNotification('किटमध्ये कोणतेही उत्पादन नाही', 'warning');
    }
}

/**
 * Get rate field HTML based on admin status
 */
function getRateFieldHTML(rateValue = '') {
    if (isAdmin) {
        return `<input type="number" step="0.01" name="rate[]" class="form-control rate-input" value="${rateValue}" onchange="calculateTotals()">`;
    } else {
        return `<input type="text" class="form-control rate-input" value="₹${parseFloat(rateValue || 0).toFixed(2)}" readonly>
                <input type="hidden" name="rate[]" class="hidden-rate" value="${rateValue}">`;
    }
}

/**
 * Initialize product data from select options
 */
function initializeProductData() {
    const productSelects = document.querySelectorAll('.product-select');
    productSelects.forEach(select => {
        select.querySelectorAll('option').forEach(option => {
            if (option.value) {
                productData[option.value] = {
                    rate: parseFloat(option.dataset.rate) || 0,
                    cml: option.dataset.cml || '',
                    unit: option.dataset.unit || 'piece'
                };
            }
        });
    });
}

/**
 * Update product info when selection changes
 */
function updateProductInfo(select) {
    const row = select.closest('.item-row');
    const selectedOption = select.options[select.selectedIndex];

    if (selectedOption && selectedOption.value) {
        const rate = selectedOption.dataset.rate || 0;
        const cml = selectedOption.dataset.cml || '';

        const rateInput = row.querySelector('.rate-input');
        const hiddenRate = row.querySelector('.hidden-rate');
        const cmlInput = row.querySelector('.cml-input');

        if (rateInput) {
            if (isAdmin) {
                rateInput.value = rate;
            } else {
                rateInput.value = rate ? '₹' + parseFloat(rate).toFixed(2) : '';
                if (hiddenRate) hiddenRate.value = rate;
            }
        }

        if (cmlInput) {
            cmlInput.value = cml;
        }
    } else {
        const rateInput = row.querySelector('.rate-input');
        const hiddenRate = row.querySelector('.hidden-rate');
        const cmlInput = row.querySelector('.cml-input');

        if (rateInput) {
            if (isAdmin) {
                rateInput.value = '';
            } else {
                rateInput.value = '';
                if (hiddenRate) hiddenRate.value = '';
            }
        }

        if (cmlInput) {
            cmlInput.value = '';
        }
    }

    calculateTotals();
}

/**
 * Add new item row to quotation
 */
function addNewItemRow() {
    const container = document.getElementById('itemsContainer');
    if (!container) return;

    // Get products from the first row or from server data
    const productOptions = getProductOptions();

    const newRow = document.createElement('div');
    newRow.className = 'item-row border rounded p-3 mb-3';
    newRow.dataset.row = Date.now();

    newRow.innerHTML = `
        <div class="row align-items-end">
            <div class="col-md-4 mb-3">
                <label class="form-label">उत्पादन *</label>
                <select class="form-select product-select" name="product_id[]" required onchange="updateProductInfo(this)">
                    <option value="">उत्पादन निवडा</option>
                    ${productOptions}
                </select>
            </div>
            <div class="col-md-2 mb-3">
                <label class="form-label">CML नं.</label>
                <input type="text" class="form-control cml-input" readonly>
            </div>
            <div class="col-md-2 mb-3">
                <label class="form-label">साईझ</label>
                <input type="text" class="form-control" name="size[]" placeholder="उदा. 63mm">
            </div>
            <div class="col-md-2 mb-3">
                <label class="form-label">प्रमाण *</label>
                <input type="number" class="form-control quantity-input" name="quantity[]" min="1" value="1" required onchange="calculateTotals()">
            </div>
            <div class="col-md-2 mb-3">
                <label class="form-label">दर (₹)</label>
                ${getRateFieldHTML()}
            </div>
        </div>
        <div class="row">
            <div class="col-12 text-end">
                <button type="button" class="btn btn-danger btn-sm remove-item" onclick="removeItemRow(this)">
                    <i class="fas fa-trash"></i> काढून टाका
                </button>
            </div>
        </div>
    `;

    container.appendChild(newRow);

    // Re-initialize event listeners
    initializeProductSelects();
    calculateTotals();
}

/**
 * Get product options HTML from existing selects or data
 */
function getProductOptions() {
    const existingSelects = document.querySelectorAll('.product-select');
    if (existingSelects.length > 0) {
        // Get options from first select (excluding the first empty option)
        const options = Array.from(existingSelects[0].options).slice(1);
        return options.map(opt => opt.outerHTML).join('');
    }
    return '';
}

/**
 * Remove item row
 */
function removeItemRow(button) {
    const row = button.closest('.item-row');
    const container = document.getElementById('itemsContainer');

    if (container && container.querySelectorAll('.item-row').length > 1) {
        row.remove();
        calculateTotals();
    } else {
        showNotification('किमान एक उत्पादन आवश्यक आहे', 'warning');
    }
}

/**
 * Initialize product select event listeners
 */
function initializeProductSelects() {
    document.querySelectorAll('.product-select').forEach(select => {
        select.removeEventListener('change', handleProductChange);
        select.addEventListener('change', handleProductChange);
    });

    document.querySelectorAll('.quantity-input').forEach(input => {
        input.removeEventListener('input', handleQuantityChange);
        input.addEventListener('input', handleQuantityChange);
    });
}

/**
 * Handle product selection change
 */
function handleProductChange(e) {
    updateProductInfo(e.target);
}

/**
 * Handle quantity change
 */
function handleQuantityChange(e) {
    calculateTotals();
}

/**
 * Calculate all totals
 */
function calculateTotals() {
    let subTotal = 0;

    document.querySelectorAll('.item-row').forEach(row => {
        const select = row.querySelector('.product-select');
        const quantityInput = row.querySelector('.quantity-input');

        if (!quantityInput) return;

        const quantity = parseFloat(quantityInput.value) || 0;

        // Get rate value based on admin status
        let rate = 0;

        if (isAdmin) {
            const rateInput = row.querySelector('input[name="rate[]"]');
            rate = parseFloat(rateInput ? rateInput.value : 0) || 0;
        } else {
            const hiddenRate = row.querySelector('.hidden-rate');
            if (hiddenRate) {
                rate = parseFloat(hiddenRate.value) || 0;
            } else if (select) {
                const selectedOption = select.options[select.selectedIndex];
                rate = parseFloat(selectedOption ? selectedOption.dataset.rate : 0) || 0;
            }
        }

        subTotal += rate * quantity;
    });

    const discountInput = document.getElementById('discountInput');
    const discountPercent = discountInput ? (parseFloat(discountInput.value) || 0) : 0;

    const discountAmount = (subTotal * discountPercent) / 100;
    const taxableAmount = subTotal - discountAmount;
    const cgst = (taxableAmount * 2.5) / 100;
    const sgst = (taxableAmount * 2.5) / 100;
    const gstTotal = cgst + sgst;
    const grandTotal = taxableAmount + gstTotal;
    const roundOff = Math.round(grandTotal) - grandTotal;
    const finalAmount = Math.round(grandTotal);

    // Update display elements
    updateDisplayValue('subTotal', subTotal);
    updateDisplayValue('discountPercent', discountPercent, '%');
    updateDisplayValue('discountAmount', discountAmount);
    updateDisplayValue('taxableAmount', taxableAmount);
    updateDisplayValue('cgstAmount', cgst);
    updateDisplayValue('sgstAmount', sgst);
    updateDisplayValue('totalGst', gstTotal);
    updateDisplayValue('roundOff', roundOff);
    updateDisplayValue('finalAmount', finalAmount);

    // Update amount in words
    const amountInWordsEl = document.getElementById('amountInWords');
    if (amountInWordsEl) {
        amountInWordsEl.textContent = numberToWords(finalAmount) + ' रुपये फक्त';
    }

    // Update grand total if exists
    const grandTotalEl = document.getElementById('grandTotal');
    if (grandTotalEl) {
        grandTotalEl.textContent = '₹' + finalAmount.toFixed(2);
    }
}

/**
 * Update display value with currency format
 */
function updateDisplayValue(elementId, value, suffix = '') {
    const element = document.getElementById(elementId);
    if (element) {
        if (elementId === 'discountPercent') {
            element.textContent = value.toFixed(2) + (suffix || '');
        } else if (elementId === 'roundOff') {
            const sign = value >= 0 ? '+' : '';
            element.textContent = sign + value.toFixed(2);
        } else {
            element.textContent = '₹' + value.toFixed(2);
        }
    }
}

/**
 * Convert number to words in Marathi
 */
function numberToWords(num) {
    if (num === 0) return 'शून्य';

    const ones = ['', 'एक', 'दोन', 'तीन', 'चार', 'पाच', 'सहा', 'सात', 'आठ', 'नऊ'];
    const teens = ['दहा', 'अकरा', 'बारा', 'तेरा', 'चौदा', 'पंधरा', 'सोळा', 'सतरा', 'अठरा', 'एकोणीस'];
    const tens = ['', '', 'वीस', 'तीस', 'चाळीस', 'पन्नास', 'साठ', 'सत्तर', 'ऐंशी', 'नव्वद'];

    function convertLessThanOneThousand(n) {
        if (n === 0) return '';
        if (n < 10) return ones[n];
        if (n < 20) return teens[n - 10];
        if (n < 100) {
            return tens[Math.floor(n / 10)] + (n % 10 !== 0 ? ' ' + ones[n % 10] : '');
        }
        return ones[Math.floor(n / 100)] + 'शे' + (n % 100 !== 0 ? ' ' + convertLessThanOneThousand(n % 100) : '');
    }

    if (num < 1000) {
        return convertLessThanOneThousand(num);
    }
    if (num < 100000) {
        return convertLessThanOneThousand(Math.floor(num / 1000)) + ' हजार' +
            (num % 1000 !== 0 ? ' ' + convertLessThanOneThousand(num % 1000) : '');
    }
    if (num < 10000000) {
        return convertLessThanOneThousand(Math.floor(num / 100000)) + ' लाख' +
            (num % 100000 !== 0 ? ' ' + numberToWords(num % 100000) : '');
    }
    return convertLessThanOneThousand(Math.floor(num / 10000000)) + ' कोटी' +
        (num % 10000000 !== 0 ? ' ' + numberToWords(num % 10000000) : '');
}

/**
 * Validate quotation form before submission
 */
function validateQuotationForm(e) {
    const customerName = document.querySelector('input[name="customer_name"]');
    const customerMobile = document.querySelector('input[name="customer_mobile"]');
    const brand = document.querySelector('select[name="brand"]');

    let isValid = true;
    let errorMessage = '';

    // Check customer details
    if (!customerName || !customerName.value.trim()) {
        errorMessage += 'कृपया ग्राहकाचे नाव टाका\n';
        isValid = false;
    }

    if (!customerMobile || !customerMobile.value.trim()) {
        errorMessage += 'कृपया मोबाईल नंबर टाका\n';
        isValid = false;
    } else if (!/^\d{10}$/.test(customerMobile.value.trim())) {
        errorMessage += 'मोबाईल नंबर 10 अंकी असावा\n';
        isValid = false;
    }

    // Check brand
    if (!brand || !brand.value) {
        errorMessage += 'कृपया ब्रँड निवडा\n';
        isValid = false;
    }

    // Check at least one product is selected
    const productSelects = document.querySelectorAll('select[name="product_id[]"]');
    let hasProduct = false;
    productSelects.forEach(select => {
        if (select.value) hasProduct = true;
    });

    if (!hasProduct) {
        errorMessage += 'कृपया किमान एक उत्पादन निवडा\n';
        isValid = false;
    }

    if (!isValid) {
        e.preventDefault();
        alert(errorMessage);
        return false;
    }

    return true;
}

/**
 * Show notification message
 */
function showNotification(message, type = 'info') {
    // Map type to Bootstrap alert classes
    const alertType = {
        'info': 'info',
        'success': 'success',
        'warning': 'warning',
        'error': 'danger'
    }[type] || 'info';

    const notification = document.createElement('div');
    notification.className = `alert alert-${alertType} alert-dismissible fade show`;
    notification.setAttribute('role', 'alert');
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    const container = document.querySelector('.flash-messages');
    if (container) {
        container.appendChild(notification);

        // Auto dismiss
        setTimeout(() => {
            const closeBtn = notification.querySelector('.btn-close');
            if (closeBtn) closeBtn.click();
        }, 5000);
    } else {
        // Fallback to alert if no container
        alert(message);
    }
}

/**
 * Format currency
 */
function formatCurrency(amount) {
    return '₹' + parseFloat(amount || 0).toFixed(2);
}

/**
 * Format date
 */
function formatDate(dateString) {
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-IN', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    } catch (e) {
        return dateString;
    }
}

/**
 * Debounce function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * AJAX request helper
 */
function ajaxRequest(url, method = 'GET', data = null) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open(method, url, true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');

        xhr.onload = function () {
            if (xhr.status >= 200 && xhr.status < 300) {
                try {
                    resolve(JSON.parse(xhr.response));
                } catch (e) {
                    resolve(xhr.response);
                }
            } else {
                reject(new Error(xhr.statusText));
            }
        };

        xhr.onerror = () => reject(new Error('Network error'));
        xhr.send(data ? JSON.stringify(data) : null);
    });
}

// Export functions for global access
window.updateProductInfo = updateProductInfo;
window.removeItemRow = removeItemRow;
window.addNewItemRow = addNewItemRow;
window.numberToWords = numberToWords;
window.formatCurrency = formatCurrency;
window.formatDate = formatDate;
window.showNotification = showNotification;
window.ajaxRequest = ajaxRequest;
window.calculateTotals = calculateTotals;