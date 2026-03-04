"""
Конфигурация SmartGrade сервера
"""
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()


class Config:
    """Основная конфигурация приложения"""
    
    # Flask
    SECRET_KEY = os.getenv('JWT_SECRET', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('NODE_ENV', 'development') == 'development'
    
    # MongoDB
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb+srv://kana:T!2-qjMQyzpH$5M@kana.pamulvt.mongodb.net/?appName=kana')
    
    # Authentication
    JWT_SECRET = os.getenv('JWT_SECRET')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = 24
    TEACHER_PASSWORD = os.getenv('TEACHER_PASSWORD')
    
    # Gemini API - Берем ключи из переменных окружения
    GEMINI_API_KEYS = [
        os.getenv('GEMINI_API_KEY1'),
        os.getenv('GEMINI_API_KEY2'),
        os.getenv('GEMINI_API_KEY3'),
    ]
    # Убираем None значения, если в .env прописано меньше 3-х ключей
    GEMINI_API_KEYS = [k for k in GEMINI_API_KEYS if k]
    GEMINI_MODEL = 'gemini-flash-latest'
    GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models'
    
    # Current key index for rotation
    _current_key_index = 0
    
    @classmethod
    def get_gemini_key(cls):
        """Returns current Gemini API key"""
        return cls.GEMINI_API_KEYS[cls._current_key_index]
    
    @classmethod
    def rotate_gemini_key(cls):
        """Rotates to next Gemini API key and returns it"""
        cls._current_key_index = (cls._current_key_index + 1) % len(cls.GEMINI_API_KEYS)
        print(f'API key rotated to index {cls._current_key_index}')
        return cls.GEMINI_API_KEYS[cls._current_key_index]
    
    # Server
    PORT = int(os.getenv('PORT', 3000))
    HOST = os.getenv('HOST', '0.0.0.0')
    
    # Anti-cheat
    WARNING_PENALTY_PERCENT = 5  # % штрафа за каждое предупреждение
    MAX_PENALTY_PERCENT = 50     # Максимальный штраф
    
    @classmethod
    def validate(cls) -> list:
        """
        Проверяет обязательные переменные окружения.
        Возвращает список ошибок (пустой если всё OK).
        """
        errors = []
        
        if not cls.JWT_SECRET:
            errors.append('❌ Ошибка: JWT_SECRET не определён в .env файле')
        
        if not cls.TEACHER_PASSWORD:
            errors.append('❌ Ошибка: TEACHER_PASSWORD не определён в .env файле')
        
        if not cls.MONGODB_URI:
            errors.append('❌ Ошибка: MONGODB_URI не определён в .env файле')
        
        if not cls.GEMINI_API_KEYS:
            errors.append('⚠️ Внимание: GEMINI_API_KEYS не определены')
        
        return errors


# Создаём экземпляр конфигурации
config = Config()
