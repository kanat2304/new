"""
Модель теста для MongoDB
"""
from mongoengine import Document, StringField, IntField, ListField, EmbeddedDocument, EmbeddedDocumentField, BooleanField, DateTimeField
from datetime import datetime, UTC


class Question(EmbeddedDocument):
    """Вложенный документ вопроса"""
    id = IntField(required=True)
    text = StringField(required=True)  # Переименовано с 'question' для совместимости
    options = ListField(StringField(), required=True)
    correct = IntField(required=True)
    
    # Для совместимости с Node.js версией
    @property
    def question(self):
        return self.text
    
    def to_dict(self):
        """Преобразует в словарь для JSON"""
        return {
            'id': self.id,
            'question': self.text,
            'options': self.options,
            'correct': self.correct
        }
    
    def to_student_dict(self):
        """Преобразует в словарь без правильного ответа (для студента)"""
        return {
            'id': self.id,
            'question': self.text,
            'options': self.options
            # correct НЕ включаем!
        }


class Test(Document):
    """Модель теста"""
    id = StringField(required=True, unique=True, primary_key=True)
    name = StringField(required=True, default='Тест без названия')
    description = StringField(default='')
    questions = ListField(EmbeddedDocumentField(Question), default=list)
    selected_count = IntField(default=20)
    time_limit = IntField(default=900)  # 15 минут в секундах
    mode = StringField(choices=['lite', 'hard'], default='lite')
    created_at = DateTimeField(default=datetime.utcnow)
    created_by = StringField(default='teacher')
    is_active = BooleanField(default=True)
    
    meta = {
        'collection': 'tests',
        'indexes': ['id', 'created_at'],
        'auto_create_index': False
    }
    
    def to_dict(self, include_correct=True):
        """Преобразует в словарь для JSON"""
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'questions': [q.to_dict() for q in self.questions] if include_correct else [q.to_student_dict() for q in self.questions],
            'selectedCount': self.selected_count,
            'timeLimit': self.time_limit,
            'mode': self.mode,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }
        return data
    
    def to_student_dict(self):
        """Преобразует в словарь без правильных ответов (для студента)"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'timeLimit': self.time_limit,
            'mode': self.mode,
            'questions': [q.to_student_dict() for q in self.questions]
        }
    
    @classmethod
    def find_by_id(cls, test_id):
        """Находит тест по ID"""
        return cls.objects(id=test_id, is_active=True).first()
    
    @classmethod
    def get_all_active(cls):
        """Получает все активные тесты"""
        return cls.objects(is_active=True).order_by('-created_at')
