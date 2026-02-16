// SmartGrade API Configuration
// ⚠️ ВАЖНО: Этот файл содержит секретный API ключ
// Не публикуйте этот файл в публичных репозиториях!

const SMARTGRADE_CONFIG = {
    // Gemini API ключ от Google AI Studio
    // Получить ключ: https://aistudio.google.com/app/apikey
    API_KEY: 'AIzaSyDZEM55NNj9GOQC_ulW3ItYz6ZBtTwHaEU',
    
    // URL для запросов к Gemini (бесплатная версия)
    get API_URL() {
        return `https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key=${this.API_KEY}`;
    }
};
