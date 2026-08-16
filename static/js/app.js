// Cart management
let cart = {};

// Update quantity for a product
function updateQuantity(productId, change) {
    const input = document.getElementById(`qty-${productId}`);
    let currentValue = parseInt(input.value);
    let newValue = currentValue + change;
    
    if (newValue >= 0) {
        input.value = newValue;
        
        if (newValue > 0) {
            cart[productId] = newValue;
        } else {
            delete cart[productId];
        }
        
        updateOrderSummary();
    }
}

// Update order summary
function updateOrderSummary() {
    const summaryDiv = document.getElementById('orderSummary');
    const totalAmountSpan = document.getElementById('totalAmount');
    const placeOrderBtn = document.getElementById('placeOrderBtn');
    
    if (Object.keys(cart).length === 0) {
        summaryDiv.innerHTML = '<p class="empty-message">No items selected</p>';
        totalAmountSpan.textContent = '0';
        placeOrderBtn.disabled = true;
        return;
    }
    
    let html = '';
    let total = 0;
    
    for (const [productId, quantity] of Object.entries(cart)) {
        const productCard = document.querySelector(`[data-id="${productId}"]`);
        const name = productCard.querySelector('h3').textContent;
        const price = parseFloat(productCard.dataset.price);
        const itemTotal = price * quantity;
        total += itemTotal;
        
        html += `
            <div class="order-item">
                <div>
                    <div class="order-item-name">${name}</div>
                    <div class="order-item-details">Quantity: ${quantity} × ₹${price}</div>
                </div>
                <div class="order-item-price">₹${itemTotal}</div>
            </div>
        `;
    }
    
    summaryDiv.innerHTML = html;
    totalAmountSpan.textContent = total;
    placeOrderBtn.disabled = false;
}

function validateCustomerName() {
    const value = document.getElementById('customer_name').value.trim();
    if (value.length < 5) {
        return false;
    }

    const lettersOnly = value.replace(/\s+/g, '');
    return lettersOnly.length >= 5 && /^[A-Za-z\s]+$/.test(value);
}

function buildOrderPayload() {
    const customerName = document.getElementById('customer_name').value.trim();
    const orderData = {
        customer_name: customerName,
        items: []
    };

    for (const [productId, quantity] of Object.entries(cart)) {
        const productCard = document.querySelector(`[data-id="${productId}"]`);
        const name = productCard.querySelector('h3').textContent;
        const price = parseFloat(productCard.dataset.price);

        orderData.items.push({
            id: parseInt(productId),
            name: name,
            price: price,
            quantity: quantity
        });
    }

    return orderData;
}

async function submitOrderRequest() {
    const customerName = document.getElementById('customer_name').value.trim();

    if (!validateCustomerName()) {
        showError('Please enter a valid full name with at least 5 letters and no numbers.');
        return false;
    }

    if (Object.keys(cart).length === 0) {
        alert('Please select at least one item');
        return false;
    }

    const orderData = buildOrderPayload();

    try {
        const response = await fetch('/create_order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(orderData)
        });

        const data = await response.json();

        if (response.ok) {
            openPaymentModal(data);
            return true;
        }

        showError(data.error || 'Failed to create order');
        return false;
    } catch (error) {
        console.error('Error:', error);
        showError('Failed to create order. Please try again.');
        return false;
    }
}

// Place order
async function placeOrder() {
    await submitOrderRequest();
}

// Open payment modal
function openPaymentModal(orderData) {
    const modal = document.getElementById('paymentModal');
    const paymentAmount = document.getElementById('paymentAmount');
    const paymentStatus = document.getElementById('paymentStatus');
    const qrCodeImage = document.getElementById('qrCodeImage');
    const payeeName = document.getElementById('payeeName');
    const orderReferenceText = document.getElementById('orderReferenceText');

    paymentAmount.textContent = orderData.amount;
    paymentStatus.innerHTML = '';
    payeeName.textContent = orderData.payee_name;
    orderReferenceText.textContent = orderData.order_ref || 'N/A';

    const yesRadio = document.querySelector('input[name="paymentDecision"][value="yes"]');
    const noRadio = document.querySelector('input[name="paymentDecision"][value="no"]');
    if (yesRadio) yesRadio.checked = true;
    if (noRadio) noRadio.checked = false;

    qrCodeImage.src = 'data:image/png;base64,' + orderData.qr_code;
    window.currentOrderData = orderData;

    document.getElementById('transactionId').value = '';
    document.getElementById('paymentNotes').value = '';

    modal.style.display = 'block';
}

// Open UPI app directly
function openUPIApp() {
    if (window.currentOrderData && window.currentOrderData.upi_deep_link) {
        // Try to open UPI app
        window.location.href = window.currentOrderData.upi_deep_link;
        
        // Fallback for desktop
        setTimeout(() => {
            // If on desktop, show QR code instead
            alert('Please scan the QR code with your UPI app');
        }, 2000);
    }
}

async function generateNewPaymentLink() {
    const paymentStatus = document.getElementById('paymentStatus');
    paymentStatus.innerHTML = '<p class="info">Generating a new payment link...</p>';

    const customerName = document.getElementById('customer_name').value.trim();
    if (!customerName) {
        paymentStatus.innerHTML = '<p class="error">Please enter your name before creating a new payment link.</p>';
        return;
    }

    if (Object.keys(cart).length === 0) {
        paymentStatus.innerHTML = '<p class="error">Please select at least one item before retrying payment.</p>';
        return;
    }

    const orderData = buildOrderPayload();

    try {
        const response = await fetch('/create_order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(orderData)
        });

        const data = await response.json();

        if (response.ok) {
            openPaymentModal(data);
            paymentStatus.innerHTML = '<p class="info">A new payment link has been generated.</p>';
        } else {
            paymentStatus.innerHTML = '<p class="error">' + (data.error || 'Failed to generate a new payment link') + '</p>';
        }
    } catch (error) {
        console.error('Error:', error);
        paymentStatus.innerHTML = '<p class="error">Failed to generate a new payment link.</p>';
    }
}

// Confirm payment manually
async function confirmPayment() {
    const transactionId = document.getElementById('transactionId').value;
    const paymentNotes = document.getElementById('paymentNotes').value;
    const paymentStatus = document.getElementById('paymentStatus');
    const paymentDecision = document.querySelector('input[name="paymentDecision"]:checked')?.value || 'yes';
    const orderRef = document.getElementById('orderReferenceText').textContent;

    if (!window.currentOrderData) {
        paymentStatus.innerHTML = '<p class="error">Order data not found</p>';
        return;
    }

    if (paymentDecision === 'no') {
        await generateNewPaymentLink();
        return;
    }

    paymentStatus.innerHTML = '<p class="info">Confirming payment...</p>';

    try {
        const response = await fetch('/confirm_payment', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                order_id: window.currentOrderData.order_id,
                transaction_id: transactionId || orderRef,
                notes: paymentNotes || `Order Ref: ${orderRef}`
            })
        });

        const data = await response.json();

        if (response.ok) {
            closePaymentModal();
            showSuccess(data.order_id);
        } else {
            paymentStatus.innerHTML = '<p class="error">' + (data.error || 'Failed to confirm payment') + '</p>';
        }
    } catch (error) {
        console.error('Error:', error);
        paymentStatus.innerHTML = '<p class="error">Failed to confirm payment</p>';
    }
}

// Close payment modal
function closePaymentModal() {
    const modal = document.getElementById('paymentModal');
    modal.style.display = 'none';
    window.currentOrderData = null;
}

// Show success modal
function showSuccess(orderId) {
    const modal = document.getElementById('successModal');
    const successOrderId = document.getElementById('successOrderId');

    successOrderId.textContent = document.getElementById('orderReferenceText').textContent || orderId;
    modal.style.display = 'block';

    cart = {};
    document.querySelectorAll('.qty-input').forEach(input => {
        input.value = 0;
    });
    updateOrderSummary();

    document.getElementById('customer_name').value = '';
    document.getElementById('transactionId').value = '';
    document.getElementById('paymentNotes').value = '';
    window.currentOrderData = null;
}

// Show error modal
function showError(message) {
    const modal = document.getElementById('errorModal');
    const errorMessage = document.getElementById('errorMessage');
    
    errorMessage.textContent = message;
    modal.style.display = 'block';
}

// Close error modal
function closeErrorModal() {
    const modal = document.getElementById('errorModal');
    modal.style.display = 'none';
}

// Close modals when clicking outside
window.onclick = function(event) {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
}

// Close button functionality
document.querySelectorAll('.close').forEach(closeBtn => {
    closeBtn.onclick = function() {
        this.closest('.modal').style.display = 'none';
    };
});

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    updateOrderSummary();
});
