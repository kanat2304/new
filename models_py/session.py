"""
Модель сессии тестирования для MongoDB
"""
from mongoengine import Document, StringField, IntField, EmbeddedDocument, EmbeddedDocumentField, DateTimeField
from datetime import datetime, timedelta, UTC


class SessionStudent(EmbeddedDocument):
    """Вложенный документ студента для сессии"""
    last_name = StringField(db_field='lastName')
    first_name = StringField(db_field='firstName')
    group_name = StringField(db_field='groupName')
    
    def to_dict(self):
        return {
            'lastName': self.last_name,
            'firstName': self.first_name,
            'groupName': self.group_name
        }


class Session(Document):
    """Модель активной сессии тестирования"""
    id = StringField(required=True, unique=True, primary_key=True)
    student = EmbeddedDocumentField(SessionStudent, required=True)
    test_id = StringField(required=True, db_field='testId')
    start_time = DateTimeField(default=lambda: datetime.now(UTC), db_field='startTime')
    time_remaining = IntField(default=900, db_field='timeRemaining')  # в секундах
    total_time = IntField(default=900, db_field='totalTime')  # в секундах
    current_question = IntField(default=0, db_field='currentQuestion')
    total_questions = IntField(default=0, db_field='totalQuestions')
    answers_count = IntField(default=0, db_field='answersCount')
    warnings = IntField(default=0)
    status = StringField(choices=['active', 'completed', 'blocked'], default='active')
    last_update = DateTimeField(default=lambda: datetime.now(UTC), db_field='lastUpdate')
    
    meta = {
        'collection': 'sessions',
        'indexes': [
            'test_id',
            'status',
            ('test_id', 'status'),
            # TTL индекс - автоматически удаляет неактивные сессии через 10 минут
            {'fields': ['last_update'], 'expireAfterSeconds': 600}
        ],
        'auto_create_index': False
    }
    
    def to_dict(self):
        """Преобразует в словарь для JSON"""
        return {
            'id': self.id,
            'student': self.student.to_dict() if self.student else None,
            'testId': self.test_id,
            'startTime': self.start_time.isoformat() if self.start_time else None,
            'timeRemaining': self.time_remaining,
            'totalTime': self.total_time,
            'currentQuestion': self.current_question,
            'totalQuestions': self.total_questions,
            'answersCount': self.answers_count,
            'warnings': self.warnings,
            'status': self.status,
            'lastUpdate': self.last_update.isoformat() if self.last_update else None
        }
    
    def update_heartbeat(self, time_remaining=None, current_question=None, 
                         answers_count=None, warnings=None, status=None):
        """Обновляет сессию (heartbeat)"""
        if time_remaining is not None:
            self.time_remaining = time_remaining
        if current_question is not None:
            self.current_question = current_question
        if answers_count is not None:
            self.answers_count = answers_count
        if warnings is not None:
            self.warnings = warnings
        if status is not None:
            self.status = status
        self.last_update = datetime.now(UTC)
        self.save()
    
    @classmethod
    def find_active(cls):
        """Находит все активные сессии за последнюю минуту"""
        one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
        return cls.objects(
            status='active',
            last_update__gte=one_minute_ago
        ).order_by('-start_time')
    
    @classmethod
    def find_by_student(cls, last_name, first_name):
        """Находит сессии по имени студента"""
        return cls.objects(
            student__last_name=last_name,
            student__first_name=first_name
        )
    
    @classmethod
    def delete_by_student(cls, last_name, first_name):
        """Удаляет сессии по имени студента"""
        return cls.objects(
            student__last_name=last_name,
            student__first_name=first_name
        ).delete()
