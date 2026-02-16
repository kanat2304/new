// SmartGrade API Configuration
// ⚠️ ВАЖНО: API ключ теперь хранится в config.local.js
// Скопируйте config.local.example.js в config.local.js и вставьте свой ключ

const SMARTGRADE_CONFIG = {
    // API ключ загружается из config.local.js
    // Если файл отсутствует, используется демо-режим
    API_KEY: typeof SMARTGRADE_LOCAL_CONFIG !== 'undefined' ? SMARTGRADE_LOCAL_CONFIG.API_KEY : '',
    
    // URL для запросов к Gemini (бесплатная версия)
    get API_URL() {
        return `https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key=${this.API_KEY}`;
    }
};
