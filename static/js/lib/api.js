// static/js/lib/api.js
/**
 * API клієнт для FastAPI backend
 */
class JudoAPI {
    constructor() {
        this.baseURL = '/api/v1';
    }

    async request(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // ============ NEWS API ============
    async getNews({ category, search, featured, limit = 12, offset = 0 } = {}) {
        const params = new URLSearchParams();
        if (category && category !== 'all') params.set('category', category);
        if (search) params.set('search', search);
        if (featured !== undefined) params.set('featured', featured);
        params.set('limit', limit);
        params.set('offset', offset);
        return this.request(`/news?${params}`);
    }

    async getLatestNews(limit = 6) {
        return this.request(`/news/latest?limit=${limit}`);
    }

    async getNewsBySlug(slug) {
        return this.request(`/news/slug/${slug}`);
    }

    async getFeaturedNews(limit = 3) {
        return this.request(`/news/featured?limit=${limit}`);
    }

    async getNewsCategories() {
        return this.request('/news/categories');
    }

    // ============ EVENTS API ============
    async getEvents({ type, category, status, age_group, featured, from_date, to_date, limit = 50, offset = 0 } = {}) {
        const params = new URLSearchParams();
        if (type && type !== 'all') params.set('type', type);
        if (category && category !== 'all') params.set('category', category);
        if (status && status !== 'all') params.set('status', status);
        if (age_group && age_group !== 'all') params.set('age_group', age_group);
        if (featured !== undefined) params.set('featured', featured);
        if (from_date) params.set('from_date', from_date);
        if (to_date) params.set('to_date', to_date);
        params.set('limit', limit);
        params.set('offset', offset);
        return this.request(`/events?${params}`);
    }

    async getUpcomingEvents(limit = 10) {
        return this.request(`/events/upcoming?limit=${limit}`);
    }

    async getFeaturedEvents(limit = 5) {
        return this.request(`/events/featured?limit=${limit}`);
    }

    async getCurrentEvents() {
        return this.request('/events/current');
    }

    async getPastEvents(limit = 20, offset = 0) {
        return this.request(`/events/past?limit=${limit}&offset=${offset}`);
    }

    async getEventsByMonth(year, month) {
        return this.request(`/events/by-month/${year}/${month}`);
    }

    async getEventById(id) {
        return this.request(`/events/${id}`);
    }

    async getEventsStats() {
        return this.request('/events/stats/overview');
    }

    // ============ TEAM API ============
    async getTeam(category = 'all') {
        const params = category !== 'all' ? `?category=${category}` : '';
        return this.request(`/team${params}`);
    }

    async getTeamMember(id) {
        return this.request(`/team/${id}`);
    }
}

// Створюємо та експортуємо екземпляр
const api = new JudoAPI();

// Named export
export { api };

// Default export (для сумісності)
export default api;
