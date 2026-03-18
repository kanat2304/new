"""
Модель результата тестирования для MongoDB
"""
from mongoengine import Document, StringField, IntField, EmbeddedDocument, EmbeddedDocumentField, ListField, BooleanField, DateTimeField
from datetime import datetime, UTC


class Student(EmbeddedDocument):
    """Вложенный документ студента"""
    last_name = StringField(required=True, db_field='lastName')
    first_name = StringField(required=True, db_field='firstName')
    group_name = StringField(required=True, db_field='groupName')
    
    def to_dict(self):
        return {
            'lastName': self.last_name,
            'firstName': self.first_name,
            'groupName': self.group_name
        }


class AnswerDetail(EmbeddedDocument):
    """Детали ответа на вопрос"""
    question_index = IntField(db_field='questionIndex')
    question_text = StringField(db_field='questionText')
    options = ListField(StringField())
    correct_answer = IntField(db_field='correctAnswer')
    student_answer = IntField(db_field='studentAnswer')
    is_correct = BooleanField(db_field='isCorrect')
    status = StringField(choices=['correct', 'incorrect', 'skipped'])
    
    def to_dict(self):
        return {
            'questionIndex': self.question_index,
            'questionText': self.question_text,
            'options': self.options,
            'correctAnswer': self.correct_answer,
            'studentAnswer': self.student_answer,
            'isCorrect': self.is_correct,
            'status': self.status
        }


class Result(Document):
    """Модель результата тестирования"""
    id = StringField(required=True, unique=True, primary_key=True)
    student = EmbeddedDocumentField(Student, required=True)
    test_id = StringField(required=True, db_field='testId')
    test_name = StringField(default='Неизвестный тест', db_field='testName')
    score = IntField(required=True, min_value=0, max_value=100)
    correct = IntField(default=0)
    incorrect = IntField(default=0)
    skipped = IntField(default=0)
    total = IntField(required=True)
    time_used = IntField(default=0, db_field='timeUsed')  # в секундах
    date = DateTimeField(default=lambda: datetime.now(UTC))
    answers = ListField(EmbeddedDocumentField(AnswerDetail), default=list)
    warnings = IntField(default=0)
    completed_at = DateTimeField(default=lambda: datetime.now(UTC), db_field='completedAt')
    
    meta = {
        'collection': 'results',
        'indexes': ['test_id', 'student.group_name', '-date'],
        'auto_create_index': False
    }
    
    def to_dict(self):
        """Преобразует в словарь для JSON"""
        return {
            'id': self.id,
            'student': self.student.to_dict() if self.student else None,
            'testId': self.test_id,
            'testName': self.test_name,
            'score': self.score,
            'correct': self.correct,
            'incorrect': self.incorrect,
            'skipped': self.skipped,
            'total': self.total,
            'timeUsed': self.time_used,
            'date': self.date.isoformat() if self.date else None,
            'answers': [a.to_dict() for a in self.answers],
            'warnings': self.warnings,
            'completedAt': self.completed_at.isoformat() if self.completed_at else None
        }
    
    @classmethod
    def find_by_test(cls, test_id):
        """Находит результаты по ID теста"""
        return cls.objects(test_id=test_id).order_by('-date')
    
    @classmethod
    def find_by_group(cls, group_name):
        """Находит результаты по группе"""
        return cls.objects(student__group_name=group_name).order_by('-date')
    
    @classmethod
    def get_stats(cls):
        """Получает общую статистику"""
        pipeline = [
            {
                '$group': {
                    '_id': None,
                    'totalStudents': {'$sum': 1},
                    'avgScore': {'$avg': '$score'},
                    'totalViolations': {'$sum': '$warnings'},
                    'totalCorrect': {'$sum': '$correct'},
                    'totalIncorrect': {'$sum': '$incorrect'}
                }
            }
        ]
        
        results = list(cls.objects.aggregate(pipeline))
        if results:
            return {
                'totalStudents': results[0]['totalStudents'],
                'avgScore': round(results[0]['avgScore'] or 0),
                'totalViolations': results[0]['totalViolations']
            }
        return {
            'totalStudents': 0,
            'avgScore': 0,
            'totalViolations': 0
        }
    
    @classmethod
    def get_unique_tests_count(cls):
        """Получает количество уникальных тестов"""
        return len(cls.objects.distinct('test_id'))
