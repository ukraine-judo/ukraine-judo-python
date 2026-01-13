/**
 * Модуль сторінки новин
 */
import api from '../lib/api.js';  // ✅ Default import
import { formatDate, showError, showLoading, debounce } from '../shared/utils.js';

// Категорії новин
const CATEGORY_MAP = {
    'all': 'Усі категорії',
    'achievements': 'Досягнення',
    'announcements': 'Анонси',
    'partnerships': 'Партнерство',
    'federationNews': 'Новини ФДУ',
    'interviews': 'Інтерв\'ю'
};

// Кольори категорій
function getCategoryColor(category) {
    const colors = {
        'achievements': 'bg-green-100 text-green-800',
        'announcements': 'bg-blue-100 text-blue-800',
        'partnerships': 'bg-purple-100 text-purple-800',
        'federationNews': 'bg-yellow-100 text-yellow-800',
        'interviews': 'bg-pink-100 text-pink-800'
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
}

function getCategoryName(category) {
    return CATEGORY_MAP[category] || category;
}

// Створення картки новини
function createNewsCard(news) {
    return `
        <article class="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-xl transition-shadow">
            ${news.image_full_url ? `
                <img 
                    src="${news.image_full_url}" 
                    alt="${news.title}" 
                    class="w-full h-48 object-cover"
                    onerror="this.style.display='none'"
                >
            ` : ''}
            
            <div class="p-6">
                <div class="flex justify-between items-center mb-3">
                    <span class="inline-block px-3 py-1 text-xs font-semibold rounded-full ${getCategoryColor(news.category)}">
                        ${getCategoryName(news.category)}
                    </span>
                    <span class="text-sm text-gray-500">
                        ${news.published_date_formatted || formatDate(news.publishedAt)}
                    </span>
                </div>
                
                <h3 class="text-xl font-bold text-gray-800 mb-2 line-clamp-2">
                    ${news.title}
                </h3>
                
                <p class="text-gray-600 mb-4 line-clamp-3">
                    ${news.excerpt}
                </p>
                
                ${news.tags_list && news.tags_list.length > 0 ? `
                    <div class="flex flex-wrap gap-2 mb-4">
                        ${news.tags_list.slice(0, 3).map(tag => `
                            <span class="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                                #${tag}
                            </span>
                        `).join('')}
                    </div>
                ` : ''}
                
                <div class="flex justify-between items-center border-t pt-4">
                    <span class="text-sm text-gray-500">${news.author_name}</span>
                    <a 
                        href="/news/${news.id}" 
                        class="text-blue-600 hover:text-blue-800 font-medium"
                    >
                        Читати далі →
                    </a>
                </div>
            </div>
        </article>
    `;
}

// Завантаження новин для попереднього перегляду (головна сторінка)
export async function loadNewsPreview(containerId = 'news-container', limit = 6) {
    const container = document.getElementById(containerId);
    if (!container) return;

    showLoading(container);

    try {
        const news = await api.getLatestNews(limit);
        
        if (news.length === 0) {
            container.innerHTML = '<p class="col-span-full text-center text-gray-500">Новин поки немає</p>';
            return;
        }

        container.innerHTML = news.map(item => createNewsCard(item)).join('');
    } catch (error) {
        console.error('Error loading news preview:', error);
        showError(container, 'Не вдалося завантажити новини');
    }
}

// Завантаження повного списку новин (сторінка новин)
export async function loadNewsList({ category = 'all', search = '', limit = 12, offset = 0 } = {}) {
    const container = document.getElementById('news-list');
    if (!container) return;

    showLoading(container);

    try {
        const news = await api.getNews({ category, search, limit, offset });
        
        if (news.length === 0) {
            container.innerHTML = '<p class="col-span-full text-center text-gray-500">Новин не знайдено</p>';
            return;
        }

        container.innerHTML = news.map(item => createNewsCard(item)).join('');
        
        // Оновлюємо пагінацію
        updatePagination(offset / limit + 1, news.length < limit);
        
    } catch (error) {
        console.error('Error loading news list:', error);
        showError(container, 'Не вдалося завантажити новини');
    }
}

// Пагінація
function updatePagination(currentPage, isLastPage) {
    const pagination = document.getElementById('pagination');
    if (!pagination) return;

    let html = '';
    
    if (currentPage > 1) {
        html += `
            <button 
                onclick="window.newsModule.loadPage(${currentPage - 1})" 
                class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
            >
                ← Назад
            </button>
        `;
    }
    
    html += `<span class="px-4 py-2 bg-gray-200 rounded font-medium">Сторінка ${currentPage}</span>`;
    
    if (!isLastPage) {
        html += `
            <button 
                onclick="window.newsModule.loadPage(${currentPage + 1})" 
                class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
            >
                Вперед →
            </button>
        `;
    }
    
    pagination.innerHTML = html;
}

// Фільтрація за категорією
export function filterByCategory(category) {
    loadNewsList({ category, limit: 12, offset: 0 });
}

// Пошук
export const searchNews = debounce((query) => {
    loadNewsList({ search: query, limit: 12, offset: 0 });
}, 300);

// Завантаження сторінки
export function loadPage(page) {
    const limit = 12;
    const offset = (page - 1) * limit;
    loadNewsList({ limit, offset });
}

// Експорт для глобального доступу
window.newsModule = {
    loadNewsPreview,
    loadNewsList,
    filterByCategory,
    searchNews,
    loadPage
};
