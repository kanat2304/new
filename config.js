// SmartGrade API Configuration
const SMARTGRADE_CONFIG = {
    // Безопасная проверка: берем ключ из локального конфига, если он есть
    API_KEY: typeof SMARTGRADE_LOCAL_CONFIG !== 'undefined' ? SMARTGRADE_LOCAL_CONFIG.API_KEY : '',
    
    // URL для запросов к Gemini
    get API_URL() {
        return `https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key=${this.API_KEY}`;
    }
};