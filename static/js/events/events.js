/**
 * Модуль сторінки календаря подій
 */
import api from '../lib/api.js';

// Поточний стан
let currentState = {
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1,
    filters: {
        type: 'all',
        category: 'all',
        status: 'all',
        age_group: 'all'
    },
    allEvents: []
};

// Назви місяців українською
const MONTHS_UK = {
    1: 'Січень', 2: 'Лютий', 3: 'Березень', 4: 'Квітень',
    5: 'Травень', 6: 'Червень', 7: 'Липень', 8: 'Серпень',
    9: 'Вересень', 10: 'Жовтень', 11: 'Листопад', 12: 'Грудень'
};

// Назви місяців у родовому відмінку
const MONTHS_UK_GENITIVE = {
    1: 'січня', 2: 'лютого', 3: 'березня', 4: 'квітня',
    5: 'травня', 6: 'червня', 7: 'липня', 8: 'серпня',
    9: 'вересня', 10: 'жовтня', 11: 'листопада', 12: 'грудня'
};

const LABELS = {
    type: {
        international: 'Міжнародні',
        national: 'Національні'
    },
    category: {
        championship: 'Чемпіонат',
        cup: 'Кубок',
        tournament: 'Турнір',
        seminar: 'Семінар',
        university: 'Університетські',
        training: 'НТЗ'
    },
    status: {
        planned: 'Заплановано',
        ongoing: 'Триває',
        finished: 'Завершено',
        canceled: 'Скасовано',
        cancelled: 'Скасовано'
    },
    age: {
        adults: 'Дорослі',
        veterans: 'Ветерани',
        officials: 'Офіційні особи',
        U23: 'До 23 років (U23)',
        U21: 'До 21 року (U21)',
        U18: 'До 18 років (U18)',
        U17: 'До 17 років (U17)',
        U16: 'До 16 років (U16)',
        U15: 'До 15 років (U15)',
        U13: 'До 13 років (U13)',
        U12: 'До 12 років (U12)'
    }
};


// Кольори для типів
function getTypeBadgeClass(type) {
    return type === 'international' 
        ? 'bg-primary-100 text-primary-700' 
        : 'bg-accent-100 text-accent-700';
}

// Іконки для категорій
function getCategoryIcon(category) {
    const icons = {
        'training': '🏕️',
        'tournament': '🥋',
        'championship': '🏆',
        'cup': '🏆',
        'seminar': '👨‍⚖️',
        'university': '🎓'
    };
    return icons[category] || '📅';
}

// Створення картки події
function createEventCard(event) {
    const typeBadgeClass = getTypeBadgeClass(event.type);
    const categoryIcon = getCategoryIcon(event.category);
    
    const isCancelled = event.status === 'cancelled' || event.status === 'canceled';
    const isFeatured = event.featured;
    const isOngoing = event.status === 'ongoing'; // ✅ Поточна подія
    
    // Статус badge
    let statusBadge = '';
    if (isOngoing) {
        statusBadge = `
            <span class="Badge bg-green-100 text-green-700 flex items-center gap-1 animate-pulse">
                <span class="size-2 rounded-full bg-green-500 animate-ping absolute"></span>
                <span class="size-2 rounded-full bg-green-500"></span>
                <span class="font-black">ЗАРАЗ ТРИВАЄ</span>
            </span>
        `;
    } else if (event.status === 'finished' || event.status === 'completed') {
        statusBadge = `<span class="Badge">${LABELS.status.finished}</span>`;
    } else if (isCancelled) {
        statusBadge = `<span class="Badge bg-red-100 text-red-700">${LABELS.status.canceled}</span>`;
    } else {
        statusBadge = `<span class="Badge">${LABELS.status.planned}</span>`;
    }
    
    // ✅ ОСОБЛИВИЙ ДИЗАЙН для поточних подій
    const ongoingStyles = isOngoing ? `
        border-2 border-green-500 
        shadow-2xl shadow-green-500/30
        ring-4 ring-green-100
        animate-pulse-slow
        bg-gradient-to-br from-green-50 to-white
    ` : '';
    
    const cardBorderClass = isFeatured && !isOngoing 
        ? 'border-2 border-primary-500 shadow-xl' 
        : isOngoing 
            ? ongoingStyles 
            : 'border-gray-200 shadow-md';
    
    return `
        <article class="group relative flex flex-col bg-white rounded-2xl border ${cardBorderClass} overflow-hidden transition-all hover:shadow-xl ${isCancelled ? 'opacity-70 hover:opacity-100' : ''}">
            
            ${isOngoing ? `
            <!-- ✅ LIVE Banner для поточних подій -->
            <div class="absolute top-0 left-0 right-0 bg-gradient-to-r from-green-500 via-green-400 to-green-500 text-white text-xs font-black uppercase tracking-widest px-4 py-2 flex items-center justify-center gap-2 z-10 animate-gradient">
                <span>ПОДІЯ ВІДБУВАЄТЬСЯ ЗАРАЗ</span>
            </div>
            ` : isFeatured ? `
            <div class="absolute top-0 right-0 bg-accent-500 text-white text-[10px] font-black uppercase tracking-widest px-3 py-1.5 rounded-bl-xl z-10 flex items-center gap-1">
                <span class="material-symbols-outlined text-[14px]">star</span>
                Виділена
            </div>
            ` : ''}

            <div class="p-6 flex-1 flex flex-col gap-4 ${isOngoing ? 'pt-14' : ''}">
                <div class="flex justify-between items-start ${isFeatured && !isOngoing ? 'pt-2' : ''}">
                    <div class="flex flex-col gap-2">
                        <div class="flex gap-2 flex-wrap">
                            <span class="Badge ${typeBadgeClass}">
                                ${event.type_label || LABELS.type[event.type] || event.type}
                            </span>
                            ${statusBadge}
                        </div>
                    </div>
                    
                    <div class="text-4xl ${isCancelled ? 'grayscale' : ''} ${isOngoing ? 'animate-bounce-slow' : ''}">
                        ${categoryIcon}
                    </div>
                </div>

                <div>
                    <h3 class="text-xl font-bold leading-tight group-hover:text-primary-600 transition-colors mb-2 ${isCancelled ? 'text-gray-500 line-through decoration-red-500/50' : ''} ${isOngoing ? 'text-green-700' : ''}">
                        ${event.title}
                    </h3>
                    ${event.description ? `
                        <p class="text-sm text-gray-600 line-clamp-2">
                            ${event.description}
                        </p>
                    ` : `
                        <p class="text-sm text-gray-400 italic">
                            Опис відсутній
                        </p>
                    `}
                </div>

                <div class="flex flex-col gap-2 mt-auto ${isCancelled ? 'grayscale opacity-70' : ''}">
                    <div class="flex items-center gap-2 text-sm ${isOngoing ? 'text-green-700 font-bold' : 'text-gray-700'}">
                        <span class="material-symbols-outlined ${isOngoing ? 'text-green-600' : 'text-primary-600'} text-[20px]">calendar_month</span>
                        <span class="font-medium">${event.date_range_formatted || event.date_formatted}</span>
                    </div>
                    <div class="flex items-center gap-2 text-sm ${isOngoing ? 'text-green-700 font-bold' : 'text-gray-700'}">
                        <span class="material-symbols-outlined ${isOngoing ? 'text-green-600' : 'text-primary-600'} text-[20px]">location_on</span>
                        <span class="font-medium">${event.location}</span>
                    </div>
                </div>

                <div class="Pills pt-2 border-t border-dashed ${isOngoing ? 'border-green-300' : 'border-gray-200'}">
                    <span class="Pill text-xs ${isOngoing ? 'bg-green-100 text-green-700 border-green-300' : ''}">${event.category_label || LABELS.category[event.category] || event.category}</span>
                    <span class="Pill text-xs ${isOngoing ? 'bg-green-100 text-green-700 border-green-300' : ''}">${event.age_group_label || LABELS.age[event.ageGroup] || event.ageGroup}</span>
                </div>
            </div>

            <div class="p-4 ${isOngoing ? 'bg-green-50 border-t border-green-200' : 'bg-gray-50 border-t border-gray-100'} flex gap-3">
                ${isCancelled ? `
                    <a href="/events/${event.id}" 
                       class="flex-1 h-11 rounded-xl border-2 border-gray-300 hover:bg-gray-100 text-gray-700 text-sm font-bold flex items-center justify-center gap-2 transition-all">
                        Причина
                    </a>
                ` : `
                    <a href="/events/${event.id}" 
                       class="flex-1 h-11 rounded-xl ${isOngoing ? 'bg-green-600 hover:bg-green-700 text-white shadow-lg shadow-green-500/30 animate-pulse-slow' : isFeatured ? 'bg-primary-600 hover:bg-primary-700 text-white shadow-lg shadow-primary-500/30' : 'bg-gray-100 hover:bg-primary-50 text-brand-700'} text-sm font-bold flex items-center justify-center gap-2 transition-all">
                        ${isOngoing ? 'Детальніше' : 'Детальніше'}
                        ${isOngoing ? '<span class="material-symbols-outlined text-[18px]">arrow_forward</span>' : isFeatured ? '<span class="material-symbols-outlined text-[18px]">arrow_forward</span>' : ''}
                    </a>
                    
                    ${event.regulation_full_url ? `
                        <a href="${event.regulation_full_url}" 
                           target="_blank"
                           class="size-11 rounded-xl border-2 ${isOngoing ? 'border-green-200 bg-white hover:bg-green-50 hover:border-green-400 text-green-700' : 'border-gray-200 bg-white hover:bg-gray-50 hover:border-primary-300 text-gray-700'} flex items-center justify-center transition-all" 
                           title="Завантажити положення">
                            <span class="material-symbols-outlined text-[20px]">description</span>
                        </a>
                    ` : `
                        <button class="size-11 rounded-xl border border-gray-200 bg-gray-50 text-gray-300 flex items-center justify-center cursor-not-allowed" 
                                disabled 
                                title="Положення відсутнє">
                            <span class="material-symbols-outlined text-[20px]">description</span>
                        </button>
                    `}
                `}
            </div>
        </article>
    `;
}


// Форматування дат
function formatDate(dateStr) {
    const date = new Date(dateStr);
    const day = date.getDate();
    const month = MONTHS_UK_GENITIVE[date.getMonth() + 1];
    const year = date.getFullYear();
    return `${day} ${month} ${year}`;
}

function formatDateRange(event) {
    if (!event.endDate) {
        return formatDate(event.date);
    }
    
    const startDate = new Date(event.date);
    const endDate = new Date(event.endDate);
    
    if (startDate.toDateString() === endDate.toDateString()) {
        return formatDate(event.date);
    }
    
    if (startDate.getMonth() === endDate.getMonth() && startDate.getFullYear() === endDate.getFullYear()) {
        const month = MONTHS_UK_GENITIVE[startDate.getMonth() + 1];
        return `${startDate.getDate()}-${endDate.getDate()} ${month} ${startDate.getFullYear()}`;
    }
    
    return `${formatDate(event.date)} - ${formatDate(event.endDate)}`;
}

// ✅ Функція визначення статусу події по даті
function determineEventStatus(event) {
    // Якщо подія скасована, залишаємо цей статус
    if (event.status === 'canceled' || event.status === 'cancelled') {
        return 'canceled';
    }
    
    const today = new Date();
    today.setHours(0, 0, 0, 0); // Скидаємо час для коректного порівняння
    
    const startDate = new Date(event.date);
    startDate.setHours(0, 0, 0, 0);
    
    let endDate = startDate;
    if (event.endDate) {
        endDate = new Date(event.endDate);
        endDate.setHours(0, 0, 0, 0);
    }
    
    // Визначаємо статус
    if (startDate <= today && today <= endDate) {
        return 'ongoing'; // Подія зараз відбувається
    } else if (today > endDate) {
        return 'finished'; // Подія завершилась
    } else {
        return 'planned'; // Подія ще не почалась
    }
}

// Підготовка даних події
function prepareEventData(event) {
    // ✅ АВТОМАТИЧНО ВИЗНАЧАЄМО СТАТУС
    const actualStatus = determineEventStatus(event);
    
    return {
        ...event,
        status: actualStatus, // Перезаписуємо статус актуальним
        type_label: LABELS.type[event.type] || event.type,
        category_label: LABELS.category[event.category] || event.category,
        age_group_label: LABELS.age[event.ageGroup] || event.ageGroup,
        date_formatted: formatDate(event.date),
        date_range_formatted: formatDateRange(event),
        regulation_full_url: event.regulationLink ? `/static/${event.regulationLink}` : null
    };
}


// Оновлення навігаційних кнопок
function updateNavigationButtons() {
    const prevBtn = document.getElementById('prev-month-btn');
    const currentBtn = document.getElementById('current-month-btn');
    const nextBtn = document.getElementById('next-month-btn');
    const title = document.getElementById('current-month-title');
    
    if (prevBtn) {
        let prevMonth = currentState.month - 1;
        let prevYear = currentState.year;
        if (prevMonth < 1) {
            prevMonth = 12;
            prevYear--;
        }
        prevBtn.textContent = `${MONTHS_UK[prevMonth]} ${prevYear}`;
    }
    
    if (currentBtn) {
        currentBtn.textContent = `${MONTHS_UK[currentState.month]} ${currentState.year}`;
    }
    
    if (title) {
        title.textContent = `${MONTHS_UK[currentState.month]} ${currentState.year}`;
    }
    
    if (nextBtn) {
        let nextMonth = currentState.month + 1;
        let nextYear = currentState.year;
        if (nextMonth > 12) {
            nextMonth = 1;
            nextYear++;
        }
        nextBtn.textContent = `${MONTHS_UK[nextMonth]} ${nextYear}`;
    }
}

// Оновлення кількості подій
function updateEventsCount(count) {
    const countEl = document.getElementById('events-count');
    if (countEl) {
        const span = countEl.querySelector('span');
        if (span) {
            span.textContent = count;
        }
    }
}

// Показати loader
function showLoading() {
    const container = document.getElementById('events-list');
    if (!container) return;
    
    container.innerHTML = `
        <div class="col-span-full flex justify-center items-center py-20">
            <div class="flex flex-col items-center gap-4">
                <div class="size-12 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin"></div>
                <p class="text-gray-600 font-medium">Завантаження подій...</p>
            </div>
        </div>
    `;
}

async function loadEvents(filters, scrollToTop = true) {
    showLoader();
    
    try {
        // ✨ Будуємо URL з урахуванням пошуку
        let url = `/calendar?year=${filters.year}`;
        
        // Додаємо month тільки якщо немає пошуку
        if (filters.month && !filters.search) {
            url += `&month=${filters.month}`;
        }
        
        if (filters.search) url += `&search=${encodeURIComponent(filters.search)}`;
        if (filters.status && filters.status !== 'all') url += `&status=${filters.status}`;
        if (filters.type && filters.type !== 'all') url += `&type=${filters.type}`;
        if (filters.category && filters.category !== 'all') url += `&category=${filters.category}`;
        
        const response = await fetch(url, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        
        if (!response.ok) throw new Error('Network error');
        
        const html = await response.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        
        const newContainer = doc.querySelector('#events-container');
        const currentContainer = document.querySelector('#events-container');
        
        if (!currentContainer || !newContainer) {
            hideLoader();
            return;
        }
        
        currentContainer.classList.add('loading');
        
        setTimeout(() => {
            currentContainer.outerHTML = newContainer.outerHTML;
            
            if (scrollToTop) {
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
            
            hideLoader();
        }, 300);
        
        updateURL(filters);
        
        // ✨ Оновлюємо currentFilters
        currentFilters = { ...currentFilters, ...filters };
        
    } catch (error) {
        console.error('Error loading events:', error);
        hideLoader();
        window.location.href = url;
    }
}


// Застосування фільтрів на клієнті
function applyClientFilters(events) {
    console.log('🔍 Applying filters:', currentState.filters); // ✅ ДЕБАГ
    console.log('🔍 Total events before filter:', events.length); // ✅ ДЕБАГ
    
    const filtered = events.filter(event => {
        console.log('🔍 Event:', event.title, {
            type: event.type,
            category: event.category,
            status: event.status,
            ageGroup: event.ageGroup
        }); // ✅ ДЕБАГ
        
        if (currentState.filters.type !== 'all' && event.type !== currentState.filters.type) {
            return false;
        }
        if (currentState.filters.category !== 'all' && event.category !== currentState.filters.category) {
            return false;
        }
        if (currentState.filters.status !== 'all' && event.status !== currentState.filters.status) {
            return false;
        }
        if (currentState.filters.age_group !== 'all' && event.ageGroup !== currentState.filters.age_group) {
            return false;
        }
        return true;
    });
    
    console.log('🔍 Filtered events:', filtered.length); // ✅ ДЕБАГ
    return filtered;
}


// Рендеринг подій
function renderEvents() {
    const container = document.getElementById('events-list');
    if (!container) return;
    
    const filteredEvents = applyClientFilters(currentState.allEvents);
    
    console.log('🎨 Rendering events:', filteredEvents.length);
    
    updateEventsCount(filteredEvents.length);
    
    if (filteredEvents.length === 0) {
        container.innerHTML = `
            <div class="col-span-full text-center py-16">
                <p class="text-gray-400 text-5xl mb-4">📭</p>
                <p class="text-gray-600 text-lg font-semibold mb-2">Подій на ${MONTHS_UK[currentState.month]} ${currentState.year} не знайдено</p>
                <p class="text-gray-400 text-sm">Спробуйте інший місяць або змініть фільтри</p>
            </div>
        `;
        return;
    }

    // ✅ СОРТУВАННЯ: Featured першими, потім за датою
    const sortedEvents = [...filteredEvents].sort((a, b) => {
        // Featured першими
        if (a.featured && !b.featured) return -1;
        if (!a.featured && b.featured) return 1;
        
        // Якщо обидві featured або обидві не featured, сортуємо за датою
        const dateA = new Date(a.date);
        const dateB = new Date(b.date);
        return dateA - dateB;
    });
    
    console.log('🔝 Sorted events (featured first):', sortedEvents.map(e => ({ title: e.title, featured: e.featured })));

    container.innerHTML = sortedEvents.map(event => createEventCard(event)).join('');
}

// Навігація
function previousMonth() {
    currentState.month--;
    if (currentState.month < 1) {
        currentState.month = 12;
        currentState.year--;
    }
    loadEventsByMonth();
}

function nextMonth() {
    currentState.month++;
    if (currentState.month > 12) {
        currentState.month = 1;
        currentState.year++;
    }
    loadEventsByMonth();
}

function goToPreviousMonth() {
    previousMonth();
}

function goToNextMonth() {
    nextMonth();
}

function goToCurrentMonth() {
    const now = new Date();
    currentState.year = now.getFullYear();
    currentState.month = now.getMonth() + 1;
    loadEventsByMonth();
}

// Застосувати фільтри
function applyFilters() {
    currentState.filters.type = document.getElementById('filter-type')?.value || 'all';
    currentState.filters.category = document.getElementById('filter-category')?.value || 'all';
    currentState.filters.status = document.getElementById('filter-status')?.value || 'all';
    currentState.filters.age_group = document.getElementById('filter-age-group')?.value || 'all';
    
    renderEvents();
}

// Скинути фільтри
function resetFilters() {
    currentState.filters = {
        type: 'all',
        category: 'all',
        status: 'all',
        age_group: 'all'
    };
    
    const selects = ['filter-type', 'filter-category', 'filter-status', 'filter-age-group'];
    selects.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = 'all';
    });
    
    renderEvents();
}

function reloadCurrentMonth() {
    loadEventsByMonth();
}
// Ініціалізація з SSR даними
function initEventsPageWithSSR(year, month) {
    currentState.year = year;
    currentState.month = month;
    
    updateNavigationButtons();
    
    const container = document.getElementById('events-list');
    
    try {
        const eventsDataAttr = container.getAttribute('data-events');
        
        if (eventsDataAttr && eventsDataAttr !== '[]') {
            const eventsData = JSON.parse(eventsDataAttr);
            
            console.log('✅ Events loaded via SSR:', eventsData.length);
            
            currentState.allEvents = eventsData.map(event => {
                // ✅ ВИЗНАЧАЄМО АКТУАЛЬНИЙ СТАТУС
                const actualStatus = determineEventStatus(event);
                
                return {
                    ...event,
                    status: actualStatus,
                    ageGroup: event.ageGroup || event.age_group || event.agegroup
                };
            });
            
            // СОРТУВАННЯ SSR даних
            currentState.allEvents.sort((a, b) => {
                if (a.featured && !b.featured) return -1;
                if (!a.featured && b.featured) return 1;
                const dateA = new Date(a.date);
                const dateB = new Date(b.date);
                return dateA - dateB;
            });
            
            console.log('📊 Events with updated status:', currentState.allEvents);
            
            updateEventsCount(currentState.allEvents.length);
            
        } else {
            console.log('⚠️ No SSR data, loading from API');
            loadEventsByMonth();
        }
        
    } catch (error) {
        console.error('❌ Error parsing SSR events:', error);
        loadEventsByMonth();
    }
}

function initEventsPage() {
    loadEventsByMonth();
}

// Експорт
window.eventsModule = {
    previousMonth,
    nextMonth,
    goToPreviousMonth,
    goToNextMonth,
    goToCurrentMonth,
    applyFilters,
    resetFilters,
    initEventsPage,
    initEventsPageWithSSR,
    reloadCurrentMonth,
    LABELS // ✅ Експортуємо для зовнішнього використання
};

export {
    initEventsPage,
    initEventsPageWithSSR,
    LABELS
};
