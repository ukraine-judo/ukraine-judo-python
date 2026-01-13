/**
 * Модуль сторінки команди
 */
import api from '../lib/api.js';  // ✅ Default import
import { formatDate, showError, showLoading, debounce } from '../shared/utils.js';

// Створення картки члена команди
function createTeamCard(member) {
    return `
        <div class="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-xl transition-shadow text-center p-6">
            <img 
                src="${member.photo_url || '/static/assets/placeholder-avatar.jpg'}" 
                alt="${member.name}"
                class="w-32 h-32 rounded-full mx-auto mb-4 object-cover border-4 border-blue-100"
                onerror="this.src='/static/assets/placeholder-avatar.jpg'"
            >
            <h3 class="text-lg font-bold text-gray-800 mb-1">${member.name}</h3>
            <p class="text-gray-600 mb-2">${member.role}</p>
            ${member.weight_category ? `
                <span class="inline-block px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
                    ${member.weight_category} кг
                </span>
            ` : ''}
        </div>
    `;
}

// Завантаження команди
export async function loadTeam(category = 'all') {
    const container = document.getElementById('team-container');
    if (!container) return;

    showLoading(container);

    try {
        const team = await api.getTeam(category);
        
        if (team.length === 0) {
            container.innerHTML = '<p class="col-span-full text-center text-gray-500">Спортсменів не знайдено</p>';
            return;
        }

        container.innerHTML = team.map(member => createTeamCard(member)).join('');
        
        // Оновлюємо активну кнопку фільтра
        updateActiveFilter(category);
        
    } catch (error) {
        console.error('Error loading team:', error);
        showError(container, 'Не вдалося завантажити команду');
    }
}

// Оновлення активного фільтра
function updateActiveFilter(activeCategory) {
    document.querySelectorAll('.team-filter-btn').forEach(btn => {
        const btnCategory = btn.dataset.category;
        if (btnCategory === activeCategory) {
            btn.classList.remove('bg-gray-200', 'text-gray-700');
            btn.classList.add('bg-blue-600', 'text-white');
        } else {
            btn.classList.remove('bg-blue-600', 'text-white');
            btn.classList.add('bg-gray-200', 'text-gray-700');
        }
    });
}

// Експорт для глобального доступу
window.teamModule = {
    loadTeam
};
