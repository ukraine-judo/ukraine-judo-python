/**
 * Утиліти спільні для всіх сторінок
 */

export function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('uk-UA', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

export function showError(container, message) {
    container.innerHTML = `
        <div class="col-span-full text-center py-8">
            <p class="text-red-500 text-lg mb-4">❌ ${message}</p>
            <button 
                onclick="location.reload()" 
                class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
            >
                Спробувати знову
            </button>
        </div>
    `;
}

export function showLoading(container, message = 'Завантаження...') {
    container.innerHTML = `
        <div class="col-span-full text-center py-8">
            <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
            <p class="text-gray-500">${message}</p>
        </div>
    `;
}

export function debounce(func, wait) {
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
