// АИС Справочная служба - основные скрипты

/**
 * Инициализация приложения
 */
document.addEventListener('DOMContentLoaded', function() {
    initAutoDismiss();
    initConfirmDialogs();
    initSearchShortcuts();
    initTooltips();
});

/**
 * Автоматическое скрытие уведомлений через 5 секунд
 */
function initAutoDismiss() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

/**
 * Подтверждение перед удалением
 */
function initConfirmDialogs() {
    document.querySelectorAll('[data-confirm]').forEach(function(el) {
        el.addEventListener('click', function(e) {
            if (!confirm(this.getAttribute('data-confirm'))) {
                e.preventDefault();
            }
        });
    });
}

/**
 * Горячие клавиши для поиска
 */
function initSearchShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl+K или / для фокуса на поиске
        if ((e.ctrlKey && e.key === 'k') || (e.key === '/' && !isInputFocused())) {
            e.preventDefault();
            const searchInput = document.querySelector('input[name="q"], input[type="search"]');
            if (searchInput) {
                searchInput.focus();
            }
        }
    });
}

function isInputFocused() {
    const active = document.activeElement;
    return active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.isContentEditable);
}

/**
 * Инициализация тултипов Bootstrap
 */
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(function(el) {
        new bootstrap.Tooltip(el);
    });
}

/**
 * AJAX запрос
 */
function ajaxRequest(url, method, data) {
    return fetch(url, {
        method: method || 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: data ? JSON.stringify(data) : null
    })
    .then(function(response) { return response.json(); })
    .then(function(data) { return data; })
    .catch(function(error) {
        console.error('AJAX Error:', error);
        return { status: 'error', message: 'Произошла ошибка' };
    });
}

/**
 * Форматирование номера телефона
 */
function formatPhone(phone) {
    if (!phone) return '';
    const digits = phone.replace(/\D/g, '');
    if (digits.length === 11) {
        return '+' + digits[0] + ' (' + digits.substring(1, 4) + ') ' + 
               digits.substring(4, 7) + '-' + digits.substring(7, 9) + '-' + 
               digits.substring(9, 11);
    }
    return phone;
}

/**
 * Форматирование даты
 */
function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('ru-RU') + ' ' + 
           date.toLocaleTimeString('ru-RU', {hour: '2-digit', minute: '2-digit'});
}

/**
 * Копирование в буфер обмена
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showNotification('Скопировано в буфер обмена', 'success');
    });
}

/**
 * Показ уведомления
 */
function showNotification(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-' + (type || 'info') + ' alert-dismissible fade show';
    alertDiv.role = 'alert';
    alertDiv.innerHTML = message + '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>';
    
    document.querySelector('main').insertBefore(alertDiv, document.querySelector('main').firstChild);
    
    setTimeout(function() {
        const bsAlert = new bootstrap.Alert(alertDiv);
        bsAlert.close();
    }, 3000);
}

/**
 * Маска для телефона
 */
function applyPhoneMask(input) {
    input.addEventListener('input', function(e) {
        let value = e.target.value.replace(/\D/g, '');
        if (value.length > 0) {
            if (value[0] === '8') value = '7' + value.substring(1);
            let formatted = '+' + value[0];
            if (value.length > 1) formatted += ' (' + value.substring(1, 4);
            if (value.length > 4) formatted += ') ' + value.substring(4, 7);
            if (value.length > 7) formatted += '-' + value.substring(7, 9);
            if (value.length > 9) formatted += '-' + value.substring(9, 11);
            e.target.value = formatted;
        }
    });
}

// Инициализация масок при загрузке
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('input[type="tel"]').forEach(function(input) {
        applyPhoneMask(input);
    });
});
