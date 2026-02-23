// SmartGrade API Configuration
// Этот файл содержит настройки для подключения к серверу

const API_CONFIG = {
    // Базовый URL API сервера
    // Для локальной разработки: http://localhost:3000/api
    // Для продакшена: https://your-server.com/api
    BASE_URL: window.location.hostname === 'localhost' 
        ? 'http://localhost:3000/api' 
        : `${window.location.protocol}//${window.location.host}/api`,
    
    // Таймаут запросов (мс)
    TIMEOUT: 30000,
    
    // Включить логирование запросов (для отладки)
    DEBUG: true
};

// ========== API HELPERS ==========

/**
 * Выполняет GET запрос к API
 * @param {string} endpoint - эндпоинт API (без /api префикса)
 * @returns {Promise<Object>} - ответ сервера
 */
async function apiGet(endpoint) {
    const url = `${API_CONFIG.BASE_URL}${endpoint}`;
    
    if (API_CONFIG.DEBUG) {
        console.log(`📡 GET ${url}`);
    }
    
    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (API_CONFIG.DEBUG) {
            console.log(`✅ Response:`, data);
        }
        
        return data;
    } catch (error) {
        console.error(`❌ API Error:`, error);
        return { success: false, error: error.message };
    }
}

/**
 * Выполняет POST запрос к API
 * @param {string} endpoint - эндпоинт API
 * @param {Object} body - тело запроса
 * @returns {Promise<Object>} - ответ сервера
 */
async function apiPost(endpoint, body) {
    const url = `${API_CONFIG.BASE_URL}${endpoint}`;
    
    if (API_CONFIG.DEBUG) {
        console.log(`📡 POST ${url}`, body);
    }
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(body)
        });
        
        const data = await response.json();
        
        if (API_CONFIG.DEBUG) {
            console.log(`✅ Response:`, data);
        }
        
        return data;
    } catch (error) {
        console.error(`❌ API Error:`, error);
        return { success: false, error: error.message };
    }
}

/**
 * Выполняет PUT запрос к API
 * @param {string} endpoint - эндпоинт API
 * @param {Object} body - тело запроса
 * @returns {Promise<Object>} - ответ сервера
 */
async function apiPut(endpoint, body) {
    const url = `${API_CONFIG.BASE_URL}${endpoint}`;
    
    if (API_CONFIG.DEBUG) {
        console.log(`📡 PUT ${url}`, body);
    }
    
    try {
        const response = await fetch(url, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(body)
        });
        
        const data = await response.json();
        
        if (API_CONFIG.DEBUG) {
            console.log(`✅ Response:`, data);
        }
        
        return data;
    } catch (error) {
        console.error(`❌ API Error:`, error);
        return { success: false, error: error.message };
    }
}

/**
 * Выполняет DELETE запрос к API
 * @param {string} endpoint - эндпоинт API
 * @returns {Promise<Object>} - ответ сервера
 */
async function apiDelete(endpoint) {
    const url = `${API_CONFIG.BASE_URL}${endpoint}`;
    
    if (API_CONFIG.DEBUG) {
        console.log(`📡 DELETE ${url}`);
    }
    
    try {
        const response = await fetch(url, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (API_CONFIG.DEBUG) {
            console.log(`✅ Response:`, data);
        }
        
        return data;
    } catch (error) {
        console.error(`❌ API Error:`, error);
        return { success: false, error: error.message };
    }
}

// ========== API METHODS ==========

const SmartGradeAPI = {
    // --- Tests ---
    
    // Получить все тесты
    async getTests() {
        return await apiGet('/tests');
    },
    
    // Получить тест по ID
    async getTest(testId) {
        return await apiGet(`/tests/${testId}`);
    },
    
    // Создать тест
    async createTest(testData) {
        return await apiPost('/tests', testData);
    },
    
    // Удалить тест
    async deleteTest(testId) {
        return await apiDelete(`/tests/${testId}`);
    },
    
    // --- Results ---
    
    // Получить все результаты
    async getResults(filters = {}) {
        const params = new URLSearchParams(filters).toString();
        return await apiGet(`/results${params ? '?' + params : ''}`);
    },
    
    // Получить статистику
    async getStats() {
        return await apiGet('/results/stats');
    },
    
    // Сохранить результат
    async saveResult(resultData) {
        return await apiPost('/results', resultData);
    },
    
    // --- Sessions ---
    
    // Получить активные сессии
    async getSessions() {
        return await apiGet('/sessions');
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
    
    // --- Health Check ---
    
    async checkHealth() {
        return await apiGet('/health');
    }
};

// Экспорт для использования в других файлах
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SmartGradeAPI, API_CONFIG };
}
