// SmartGrade API Configuration
// Этот файл содержит настройки для подключения к серверу

// Проверка локального хоста
const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

const API_CONFIG = {
    // Базовый URL API сервера
    // Для локальной разработки: http://localhost:3000/api
    // Для продакшена: https://your-server.com/api
    BASE_URL: (isLocalhost || window.location.protocol === 'file:') 
        ? 'http://localhost:3000/api' 
        : `${window.location.protocol}//${window.location.host}/api`,
    
    // Таймаут запросов (мс)
    TIMEOUT: 30000,
    
    // Включить логирование запросов (только для локальной разработки)
    DEBUG: isLocalhost
};

// ========== AUTH HELPERS ==========

const Auth = {
    // Получить токен из localStorage
    getToken() {
        return localStorage.getItem('auth_token');
    },
    
    // Сохранить токен
    setToken(token) {
        localStorage.setItem('auth_token', token);
    },
    
    // Удалить токен (выход)
    logout() {
        localStorage.removeItem('auth_token');
    },
    
    // Проверить, авторизован ли пользователь
    isAuthenticated() {
        return !!this.getToken();
    },
    
    // Вход (с паролем)
    async login(password) {
        const response = await apiPost('/login', { password });
        if (response.success && response.token) {
            this.setToken(response.token);
        }
        return response;
    },
    
    // Проверка токена
    async verifyToken() {
        const token = this.getToken();
        if (!token) return { success: false };
        return await apiGet('/verify-token');
    }
};

// ========== API HELPERS ==========

/**
 * Создаёт AbortController с таймаутом
 * @param {number} timeout - время в мс
 * @returns {{ controller: AbortController, timeoutId: number }}
 */
function createTimeoutController(timeout) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    return { controller, timeoutId };
}

/**
 * Возвращает заголовки с авторизацией
 * @returns {Object}
 */
function getAuthHeaders() {
    const headers = {
        'Content-Type': 'application/json'
    };
    const token = Auth.getToken();
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
}

/**
 * Выполняет fetch запрос с таймаутом и обработкой ошибок
 * @param {string} url - полный URL запроса
 * @param {Object} options - опции fetch (method, headers, body)
 * @param {boolean} requireAuth - требуется ли авторизация
 * @returns {Promise<Object>} - ответ сервера или объект ошибки
 */
async function fetchWithTimeout(url, options = {}, requireAuth = false) {
    const { controller, timeoutId } = createTimeoutController(API_CONFIG.TIMEOUT);
    
    // Добавляем заголовки авторизации
    options.headers = { ...options.headers, ...getAuthHeaders() };
    
    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        // Обработка 401 - неавторизован
        if (response.status === 401) {
            Auth.logout();
            return { success: false, error: 'Требуется авторизация', status: 401, needLogin: true };
        }
        
        if (!response.ok) {
            const errorText = await response.text().catch(() => 'Unknown error');
            if (API_CONFIG.DEBUG) {
                console.error(`❌ HTTP ${response.status}:`, errorText);
            }
            return { success: false, error: `HTTP ${response.status}`, status: response.status };
        }
        
        const data = await response.json();
        
        if (API_CONFIG.DEBUG) {
            console.log(`✅ Response:`, data);
        }
        
        return data;
    } catch (error) {
        clearTimeout(timeoutId);
        
        if (error.name === 'AbortError') {
            console.error(`❌ Request timeout after ${API_CONFIG.TIMEOUT}ms`);
            return { success: false, error: 'Request timeout', isTimeout: true };
        }
        
        console.error(`❌ API Error:`, error);
        return { success: false, error: error.message };
    }
}

/**
 * Выполняет GET запрос к API
 * @param {string} endpoint - эндпоинт API (без /api префикса)
 * @param {boolean} requireAuth - требуется ли авторизация
 * @returns {Promise<Object>} - ответ сервера
 */
async function apiGet(endpoint, requireAuth = false) {
    const url = `${API_CONFIG.BASE_URL}${endpoint}`;
    
    if (API_CONFIG.DEBUG) {
        console.log(`📡 GET ${url}`);
    }
    
    return await fetchWithTimeout(url, {
        method: 'GET'
    }, requireAuth);
}

/**
 * Выполняет POST запрос к API
 * @param {string} endpoint - эндпоинт API
 * @param {Object} body - тело запроса
 * @param {boolean} requireAuth - требуется ли авторизация
 * @returns {Promise<Object>} - ответ сервера
 */
async function apiPost(endpoint, body, requireAuth = false) {
    const url = `${API_CONFIG.BASE_URL}${endpoint}`;
    
    if (API_CONFIG.DEBUG) {
        console.log(`📡 POST ${url}`, body);
    }
    
    return await fetchWithTimeout(url, {
        method: 'POST',
        body: JSON.stringify(body)
    }, requireAuth);
}

/**
 * Выполняет PUT запрос к API
 * @param {string} endpoint - эндпоинт API
 * @param {Object} body - тело запроса
 * @param {boolean} requireAuth - требуется ли авторизация
 * @returns {Promise<Object>} - ответ сервера
 */
async function apiPut(endpoint, body, requireAuth = false) {
    const url = `${API_CONFIG.BASE_URL}${endpoint}`;
    
    if (API_CONFIG.DEBUG) {
        console.log(`📡 PUT ${url}`, body);
    }
    
    return await fetchWithTimeout(url, {
        method: 'PUT',
        body: JSON.stringify(body)
    }, requireAuth);
}

/**
 * Выполняет DELETE запрос к API
 * @param {string} endpoint - эндпоинт API
 * @param {boolean} requireAuth - требуется ли авторизация
 * @returns {Promise<Object>} - ответ сервера
 */
async function apiDelete(endpoint, requireAuth = false) {
    const url = `${API_CONFIG.BASE_URL}${endpoint}`;
    
    if (API_CONFIG.DEBUG) {
        console.log(`📡 DELETE ${url}`);
    }
    
    return await fetchWithTimeout(url, {
        method: 'DELETE'
    }, requireAuth);
}

// ========== API METHODS ==========

/**
 * Преобразует объект в query string с поддержкой вложенных объектов
 * @param {Object} obj - объект для преобразования
 * @param {string} prefix - префикс для вложенных ключей
 * @returns {string} - query string
 */
function buildQueryString(obj, prefix = '') {
    const pairs = [];
    
    for (const key in obj) {
        if (Object.prototype.hasOwnProperty.call(obj, key) && obj[key] !== undefined && obj[key] !== null) {
            const value = obj[key];
            const prefixedKey = prefix ? `${prefix}[${key}]` : key;
            
            if (typeof value === 'object' && !Array.isArray(value)) {
                // Вложенный объект - рекурсия
                pairs.push(buildQueryString(value, prefixedKey));
            } else if (Array.isArray(value)) {
                // Массив - добавляем каждый элемент
                value.forEach((item, index) => {
                    pairs.push(`${encodeURIComponent(prefixedKey)}[${index}]=${encodeURIComponent(item)}`);
                });
            } else {
                // Простое значение
                pairs.push(`${encodeURIComponent(prefixedKey)}=${encodeURIComponent(value)}`);
            }
        }
    }
    
    return pairs.join('&');
}

const SmartGradeAPI = {
    // --- Auth ---
    
    // Вход (с паролем)
    async login(password) {
        return await Auth.login(password);
    },
    
    // Выход
    logout() {
        Auth.logout();
    },
    
    // Проверка авторизации
    isAuthenticated() {
        return Auth.isAuthenticated();
    },
    
    // Проверка токена
    async verifyToken() {
        return await Auth.verifyToken();
    },
    
    // --- Tests ---
    
    // Получить все тесты (требует авторизации)
    async getTests() {
        return await apiGet('/tests', true);
    },
    
    // Получить тест по ID для учителя (с правильными ответами)
    async getTest(testId) {
        return await apiGet(`/tests/${testId}`, true);
    },
    
    // Получить тест для студента (без правильных ответов)
    async getTestForStudent(testId) {
        return await apiGet(`/tests/${testId}/student`);
    },
    
    // Создать тест (требует авторизации)
    async createTest(testData) {
        return await apiPost('/tests', testData, true);
    },
    
    // Удалить тест (требует авторизации)
    async deleteTest(testId) {
        return await apiDelete(`/tests/${testId}`, true);
    },
    
    // --- Results ---
    
    // Получить все результаты (требует авторизации)
    async getResults(filters = {}) {
        const params = buildQueryString(filters);
        return await apiGet(`/results${params ? '?' + params : ''}`, true);
    },
    
    // Получить статистику (требует авторизации)
    async getStats() {
        return await apiGet('/results/stats', true);
    },
    
    // Сохранить результат (сервер вычисляет балл)
    async saveResult(resultData) {
        return await apiPost('/results', resultData);
    },
    
    // --- Sessions ---
    
    // Получить активные сессии (требует авторизации)
    async getSessions() {
        return await apiGet('/sessions', true);
    },
    
    // Создать сессию
    async createSession(sessionData) {
        return await apiPost('/sessions', sessionData);
    },
    
    // Обновить сессию (heartbeat)
    async updateSession(sessionId, data) {
        return await apiPut(`/sessions/${sessionId}`, data);
    },
    
    // Удалить сессию
    async deleteSession(sessionId) {
        return await apiDelete(`/sessions/${sessionId}`);
    },
    
    // --- Gemini AI ---
    
     // Генерация вопросов (требует авторизации)
     async generateQuestions(text, questionCount = 20) {
         return await apiPost('/generate-questions', { text, questionCount }, true);
     },
     
     // Генерация нескольких уникальных тестов (требует авторизации)
     async generateUniqueTests(questions, testCount, options = {}) {
         return await apiPost('/generate-unique-tests', { 
             questions, 
             testCount, 
             name: options.name,
             description: options.description,
             selectedCount: options.selectedCount,
             timeLimit: options.timeLimit,
             mode: options.mode
         }, true);
     },
    
    // --- Health Check ---
    
    async checkHealth() {
        return await apiGet('/health');
    }
};

// Экспорт для использования в других файлах
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SmartGradeAPI, API_CONFIG, Auth };
}
