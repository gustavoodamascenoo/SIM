document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Equipment selection for maintenance plan in schedule form
    const equipmentSelect = document.getElementById('equipment-select');
    const planSelect = document.getElementById('plan-select');
    
    if (equipmentSelect && planSelect) {
        equipmentSelect.addEventListener('change', function() {
            const equipmentId = this.value;
            
            // Clear existing options
            planSelect.innerHTML = '<option value="">Select a plan</option>';
            
            if (equipmentId) {
                // Fetch maintenance plans for this equipment
                fetch(`/api/equipment/${equipmentId}/maintenance_plans`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }
                        return response.json();
                    })
                    .then(data => {
                        if (data && data.length > 0) {
                            // Add options for each plan
                            data.forEach(plan => {
                                const option = document.createElement('option');
                                option.value = plan.id;
                                option.textContent = plan.name;
                                planSelect.appendChild(option);
                            });
                            planSelect.disabled = false;
                        } else {
                            // No plans found
                            const option = document.createElement('option');
                            option.textContent = 'No plans available for this equipment';
                            planSelect.appendChild(option);
                            planSelect.disabled = true;
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching maintenance plans:', error);
                        const option = document.createElement('option');
                        option.textContent = 'Error loading plans';
                        planSelect.appendChild(option);
                        planSelect.disabled = true;
                    });
            }
        });
    }
    
    // Form validation for maintenance checklist
    const maintenanceForm = document.getElementById('maintenanceForm');
    if (maintenanceForm) {
        maintenanceForm.addEventListener('submit', function(event) {
            const statusSelect = document.getElementById('status');
            const endTimeInput = document.getElementById('end_time');
            
            // If status is "completed" but end time is empty, prevent submission
            if (statusSelect.value === 'completed' && endTimeInput.value === '') {
                event.preventDefault();
                alert('Please enter an end time for completed maintenance.');
                endTimeInput.focus();
            }
            
            // Check required checklist items
            const requiredItems = document.querySelectorAll('.checklist-item[data-required="true"]');
            for (const item of requiredItems) {
                const statusSelect = item.querySelector('select');
                if (statusSelect.value === 'pending' && document.getElementById('status').value === 'completed') {
                    event.preventDefault();
                    alert('All required checklist items must be completed or marked as not applicable.');
                    statusSelect.focus();
                    break;
                }
            }
        });
    }
    
    // Dynamic checklist item addition
    const addItemBtn = document.getElementById('add-item-btn');
    const itemsContainer = document.getElementById('items-container');
    
    if (addItemBtn && itemsContainer) {
        let itemCount = document.querySelectorAll('.item-card').length;
        
        addItemBtn.addEventListener('click', function() {
            const newItem = document.createElement('div');
            newItem.className = 'card mb-3 item-card';
            newItem.innerHTML = `
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-9">
                            <label class="form-label">Task Description *</label>
                            <input class="form-control" id="items-${itemCount}-description" name="items-${itemCount}-description" required type="text">
                            <input id="items-${itemCount}-order" name="items-${itemCount}-order" type="hidden" value="${itemCount+1}">
                        </div>
                        <div class="col-md-2">
                            <label class="form-label d-block">Required</label>
                            <div class="form-check form-switch">
                                <input class="form-check-input" id="items-${itemCount}-is_required" name="items-${itemCount}-is_required" checked type="checkbox" value="y">
                                <label class="form-check-label" for="items-${itemCount}-is_required">Yes</label>
                            </div>
                        </div>
                        <div class="col-md-1 d-flex align-items-end">
                            <button type="button" class="btn btn-danger remove-item">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;
            itemsContainer.appendChild(newItem);
            itemCount++;
            
            // Update the remove buttons
            updateRemoveButtons();
        });
        
        // Event delegation for removing items
        itemsContainer.addEventListener('click', function(e) {
            if (e.target.closest('.remove-item')) {
                e.target.closest('.item-card').remove();
                updateItemOrders();
                updateRemoveButtons();
            }
        });
        
        // Function to update the order hidden inputs
        function updateItemOrders() {
            const items = document.querySelectorAll('.item-card');
            items.forEach((item, index) => {
                const orderInput = item.querySelector('input[name$="-order"]');
                if (orderInput) {
                    orderInput.value = index + 1;
                }
                
                // Update the name and id attributes
                const inputs = item.querySelectorAll('input, select');
                inputs.forEach(input => {
                    const nameMatch = input.name.match(/items-(\d+)-/);
                    if (nameMatch) {
                        const oldIndex = nameMatch[1];
                        const suffix = input.name.split('-').pop();
                        input.name = `items-${index}-${suffix}`;
                        input.id = `items-${index}-${suffix}`;
                        
                        // Update label for if it exists
                        const label = item.querySelector(`label[for="items-${oldIndex}-${suffix}"]`);
                        if (label) {
                            label.setAttribute('for', `items-${index}-${suffix}`);
                        }
                    }
                });
            });
        }
        
        // Function to disable remove button if only one item
        function updateRemoveButtons() {
            const removeButtons = document.querySelectorAll('.remove-item');
            const disableButtons = removeButtons.length === 1;
            
            removeButtons.forEach(button => {
                button.disabled = disableButtons;
            });
        }
        
        // Initialize the buttons state
        updateRemoveButtons();
    }
    
    // Date range validation
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');
    
    if (startDateInput && endDateInput) {
        endDateInput.addEventListener('change', function() {
            if (startDateInput.value && this.value && new Date(this.value) < new Date(startDateInput.value)) {
                alert('End date cannot be earlier than start date');
                this.value = startDateInput.value;
            }
        });
        
        startDateInput.addEventListener('change', function() {
            if (endDateInput.value && this.value && new Date(endDateInput.value) < new Date(this.value)) {
                endDateInput.value = this.value;
            }
        });
    }
    
    // Auto-close alerts after 5 seconds
    const autoCloseAlerts = document.querySelectorAll('.alert:not(.alert-danger):not(.alert-warning)');
    autoCloseAlerts.forEach(alert => {
        setTimeout(() => {
            const closeButton = alert.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            } else {
                alert.classList.add('fade');
                setTimeout(() => {
                    alert.remove();
                }, 500);
            }
        }, 5000);
    });
});
