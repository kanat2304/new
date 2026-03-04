"""
SmartGrade Test Platform - Python Flask Server
Система тестирования с защитой от списывания
"""
import os
import json
import time
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import jwt
import requests
from mongoengine import connect, disconnect
from mongoengine.errors import DoesNotExist, NotUniqueError, ValidationError
import certifi

os.environ['SSL_CERT_FILE'] = certifi.where()

from config import config
from models_py import Test, Question, Result, Student, AnswerDetail, Session, SessionStudent


# ========== FLASK APP INITIALIZATION ==========
app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

# Enable CORS
CORS(app)

# MongoDB connection
mongo_connected = False


def connect_mongodb():
    global mongo_connected
    try:
        uri = os.getenv('MONGODB_URI')
        # Добавляем принудительный разрыв старых соединений перед новым
        disconnect() 
        
        connect(
            host=uri,
            tls=True,
            tlsAllowInvalidCertificates=True,
            serverSelectionTimeoutMS=5000
        )
        print('✅ MongoDB подключена успешно')
        mongo_connected = True
    except Exception as err:
        print(f'❌ Ошибка подключения: {err}')


# ========== JWT HELPERS ==========

def create_token(payload: dict) -> str:
    """Создаёт JWT токен"""
    payload['iat'] = int(time.time())
    payload['exp'] = int(time.time()) + (config.JWT_EXPIRATION_HOURS * 60 * 60)
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def verify_token(token: str) -> dict | None:
    """Проверяет JWT токен и возвращает payload или None"""
    if not token or not isinstance(token, str):
        return None
    
    try:
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def require_auth(f):
    """Декоратор для проверки авторизации"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'error': 'Требуется авторизация'
            }), 401
        
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        payload = verify_token(token)
        
        if not payload:
            return jsonify({
                'success': False,
                'error': 'Недействительный токен'
            }), 401
        
        request.user = payload
        return f(*args, **kwargs)
    
    return decorated_function


# ========== GEMINI API ==========

def generate_questions_with_gemini(text: str, question_count: int = 20) -> dict:
    """Генерирует вопросы с помощью Gemini API с ротацией ключей"""
    if not config.GEMINI_API_KEYS:
        return {'success': False, 'error': 'GEMINI_API_KEY не настроен на сервере'}
    
    prompt = f"""На основе следующего текста создай {question_count} тестовых вопросов с 4 вариантами ответа.

Текст документа:
{text}

ТРЕБОВАНИЯ:
1. Создай ровно {question_count} вопросов
2. Каждый вопрос должен иметь ровно 4 варианта ответа
3. Укажи индекс правильного ответа (0-3) в поле "correct"
4. Вопросы должны проверять понимание материала, а не просто память
5. Варианты ответов должны быть правдоподобными

Ответь ТОЛЬКО валидным JSON массивом в формате:
[
  {{
    "question": "Текст вопроса?",
    "options": ["Вариант 1", "Вариант 2", "Вариант 3", "Вариант 4"],
    "correct": 0
  }}
]

Без markdown, без объяснений, только JSON массив."""

    # Пытаемся пройтись по всем ключам, которые есть в конфиге
    for attempt in range(len(config.GEMINI_API_KEYS)):
        api_key = config.get_gemini_key()
        url = f"{config.GEMINI_API_URL}/{config.GEMINI_MODEL}:generateContent?key={api_key}"
        
        try:
            response = requests.post(url, json={
                'contents': [{'parts': [{'text': prompt}]}],
                'generationConfig': {
                    'temperature': 0.7,
                    'maxOutputTokens': 8192,
                    'responseMimeType': 'application/json'
                }
            }, headers={'Content-Type': 'application/json'}, timeout=30) # Добавим таймаут
            
            if not response.ok:
                error_json = {}
                try:
                    error_json = response.json()
                except:
                    pass

                error_msg = error_json.get('error', {}).get('message', '')
                error_reason = error_json.get('error', {}).get('status', '')

                # ПРОВЕРКА: Если ключ истек, заблокирован или лимит исчерпан — ротируем!
                reasons_to_rotate = ['RESOURCE_EXHAUSTED', 'INVALID_ARGUMENT', 'PERMISSION_DENIED']
                
                if error_reason in reasons_to_rotate or "API key expired" in error_msg:
                    print(f'⚠️ Ключ {config._current_key_index} не валиден или лимит исчерпан. Ротируем...')
                    config.rotate_gemini_key()
                    continue # Переходим к следующему ключу в цикле
                
                return {'success': False, 'error': f'Gemini API error: {error_msg}'}
            
            # Если дошли сюда — запрос успешен
            data = response.json()
            
            generated_text = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text')
            
            if not generated_text:
                return {'success': False, 'error': 'Пустой ответ от Gemini'}
            
            # Парсим JSON из ответа
            clean_text = generated_text.strip()
            if clean_text.startswith('```json'):
                clean_text = clean_text[7:]
            if clean_text.startswith('```'):
                clean_text = clean_text[3:]
            if clean_text.endswith('```'):
                clean_text = clean_text[:-3]
            clean_text = clean_text.strip()
            
            questions = json.loads(clean_text)
            
            if not isinstance(questions, list):
                return {'success': False, 'error': 'Ответ Gemini не является массивом'}
            
            # Валидируем структуру вопросов
            valid_questions = [
                q for q in questions
                if q.get('question') and
                   isinstance(q.get('options'), list) and
                   len(q.get('options', [])) == 4 and
                   isinstance(q.get('correct'), int) and
                   0 <= q.get('correct', -1) < 4
            ]
            
            if not valid_questions:
                return {'success': False, 'error': 'Не создано ни одного валидного вопроса'}
            
            print(f'✅ Сгенерировано {len(valid_questions)} вопросов с ключом {config._current_key_index}')
            
            return {
                'success': True,
                'questions': valid_questions,
                'generatedCount': len(valid_questions),
                'requestedCount': question_count
            }
            
        except json.JSONDecodeError as e:
            print(f'JSON parse error: {e}')
            return {
                'success': False,
                'error': 'Не удалось распарсить ответ Gemini как JSON',
                'raw': generated_text[:500] if 'generated_text' in dir() else ''
            }
        except Exception as e:
            print(f'❌ Ошибка при попытке с ключом {config._current_key_index}: {e}')
            config.rotate_gemini_key()
            continue
    
    return {'success': False, 'error': 'Все доступные API ключи не работают или просрочены.'}


# ========== API ROUTES ==========

# --- HEALTH CHECK ---
@app.route('/api/health', methods=['GET'])
def health_check():
    """Проверка работоспособности сервера"""
    return jsonify({
        'status': 'ok',
        'message': 'SmartGrade API работает',
        'timestamp': datetime.utcnow().isoformat()
    })


# --- AUTH API ---

@app.route('/api/login', methods=['POST'])
def login():
    """Вход учителя"""
    data = request.get_json() or {}
    password = data.get('password')
    
    if password == config.TEACHER_PASSWORD:
        token = create_token({'role': 'teacher'})
        return jsonify({'success': True, 'token': token})
    else:
        return jsonify({'success': False, 'error': 'Неверный пароль'}), 401


@app.route('/api/verify-token', methods=['GET'])
@require_auth
def verify_token_endpoint():
    """Проверка токена"""
    return jsonify({'success': True, 'user': request.user})


# --- GEMINI API ---

@app.route('/api/generate-questions', methods=['POST'])
@require_auth
def generate_questions():
    """Генерирует вопросы с помощью Gemini API"""
    data = request.get_json() or {}
    text = data.get('text')
    question_count = data.get('questionCount', 20)
    
    if not text:
        return jsonify({'success': False, 'error': 'Текст документа обязателен'}), 400
    
    result = generate_questions_with_gemini(text, question_count)
    
    if not result['success']:
        # Возвращаем 401 (если ключи сдохли) или 429 (если лимиты), чтобы фронт понимал суть
        status_code = 401 if "key" in result.get('error', '').lower() else 400
        return jsonify(result), status_code
    
    return jsonify(result)


# --- TESTS API ---

@app.route('/api/tests', methods=['GET'])
@require_auth
def get_tests():
    """Получить все тесты (только для авторизованных учителей)"""
    try:
        tests = Test.get_all_active()
        # Скрываем правильные ответы
        tests_data = [test.to_dict(include_correct=False) for test in tests]
        return jsonify({'success': True, 'tests': tests_data})
    except Exception as e:
        print(f'Ошибка получения тестов: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/tests/<test_id>/student', methods=['GET'])
def get_test_for_student(test_id):
    """Получить тест по ID для студента (БЕЗ правильных ответов)"""
    try:
        test = Test.find_by_id(test_id)
        
        if not test:
            return jsonify({'success': False, 'error': 'Тест не найден'}), 404
        
        return jsonify({'success': True, 'test': test.to_student_dict()})
    except Exception as e:
        print(f'Ошибка получения теста: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/tests/<test_id>', methods=['GET'])
@require_auth
def get_test(test_id):
    """Получить тест по ID для учителя (С правильными ответами)"""
    try:
        test = Test.find_by_id(test_id)
        
        if not test:
            return jsonify({'success': False, 'error': 'Тест не найден'}), 404
        
        return jsonify({'success': True, 'test': test.to_dict()})
    except Exception as e:
        print(f'Ошибка получения теста: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/tests', methods=['POST'])
@require_auth
def create_test():
    """Создать новый тест (требует авторизации)"""
    try:
        data = request.get_json() or {}
        
        test_id = data.get('id') or f'test_{int(time.time() * 1000)}'
        
        # Проверяем существование теста
        existing = Test.find_by_id(test_id)
        if existing:
            return jsonify({
                'success': False,
                'error': 'Тест с таким ID уже существует'
            }), 400
        
        # Создаём вопросы
        questions_data = data.get('questions', [])
        questions = []
        for i, q in enumerate(questions_data):
            question = Question(
                id=i,
                text=q.get('question', ''),
                options=q.get('options', []),
                correct=q.get('correct', 0)
            )
            questions.append(question)
        
        test = Test(
            id=test_id,
            name=data.get('name') or f'Тест от {datetime.now().strftime("%d.%m.%Y")}',
            description=data.get('description', ''),
            questions=questions,
            selected_count=data.get('selectedCount') or len(questions) or 20,
            time_limit=data.get('timeLimit', 900),
            mode=data.get('mode', 'lite')
        )
        
        test.save()
        
        print(f'✅ Тест создан: {test.name} ({test.id})')
        
        return jsonify({
            'success': True,
            'test': {
                'id': test.id,
                'name': test.name,
                'questionCount': len(test.questions),
                'timeLimit': test.time_limit,
                'mode': test.mode
            }
        })
    except NotUniqueError:
        return jsonify({
            'success': False,
            'error': 'Тест с таким ID уже существует'
        }), 400
    except Exception as e:
        print(f'Ошибка создания теста: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/tests/<test_id>', methods=['DELETE'])
@require_auth
def delete_test(test_id):
    """Удалить тест (требует авторизации)"""
    try:
        test = Test.objects(id=test_id).first()
        
        if not test:
            return jsonify({'success': False, 'error': 'Тест не найден'}), 404
        
        test_name = test.name
        test.delete()
        
        # Удаляем связанные результаты
        Result.objects(test_id=test_id).delete()
        
        print(f'🗑️ Тест удалён: {test_name} ({test_id})')
        
        return jsonify({'success': True, 'message': 'Тест удалён'})
    except Exception as e:
        print(f'Ошибка удаления теста: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


# --- RESULTS API ---

@app.route('/api/results', methods=['GET'])
@require_auth
def get_results():
    """Получить все результаты (требует авторизации)"""
    try:
        test_id = request.args.get('testId')
        group = request.args.get('group')
        
        query = {}
        if test_id:
            query['test_id'] = test_id
        if group:
            query['student__group_name'] = group
        
        results = Result.objects(**query).order_by('-date').limit(500)
        results_data = [r.to_dict() for r in results]
        
        return jsonify({'success': True, 'results': results_data})
    except Exception as e:
        print(f'Ошибка получения результатов: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/results/stats', methods=['GET'])
@require_auth
def get_stats():
    """Получить статистику (требует авторизации)"""
    try:
        stats = Result.get_stats()
        stats['totalTests'] = Result.get_unique_tests_count()
        
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        print(f'Ошибка получения статистики: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/results', methods=['POST'])
def submit_result():
    """
    Отправить ответы теста и получить результат (вычисление на сервере).
    Студент отправляет только свои ответы, сервер сам вычисляет балл.
    """
    try:
        data = request.get_json() or {}
        
        student_data = data.get('student', {})
        test_id = data.get('testId')
        answers = data.get('answers', [])
        time_used = data.get('timeUsed', 0)
        warnings = data.get('warnings', 0)
        
        # Получаем тест с правильными ответами
        test = Test.find_by_id(test_id)
        if not test:
            return jsonify({'success': False, 'error': 'Тест не найден'}), 404
        
        # Вычисляем результат на сервере
        correct = 0
        incorrect = 0
        skipped = 0
        answer_details = []
        
        for i, q in enumerate(test.questions):
            student_answer = answers[i] if i < len(answers) else None
            is_correct = student_answer == q.correct
            
            if student_answer is None:
                skipped += 1
                answer_details.append(AnswerDetail(
                    question_index=i,
                    student_answer=None,
                    is_correct=False,
                    status='skipped'
                ))
            elif is_correct:
                correct += 1
                answer_details.append(AnswerDetail(
                    question_index=i,
                    student_answer=student_answer,
                    is_correct=True,
                    status='correct'
                ))
            else:
                incorrect += 1
                answer_details.append(AnswerDetail(
                    question_index=i,
                    student_answer=student_answer,
                    is_correct=False,
                    status='incorrect'
                ))
        
        total = len(test.questions)
        score = round((correct / total) * 100) if total > 0 else 0
        
        # Применяем штраф за нарушения
        warning_penalty = min(warnings * config.WARNING_PENALTY_PERCENT, config.MAX_PENALTY_PERCENT)
        score = max(0, score - warning_penalty)
        
        # Создаём студента
        student = Student(
            last_name=student_data.get('lastName', ''),
            first_name=student_data.get('firstName', ''),
            group_name=student_data.get('groupName', '')
        )
        
        result = Result(
            id=f'result_{int(time.time() * 1000)}',
            student=student,
            test_id=test_id,
            test_name=test.name,
            score=score,
            correct=correct,
            incorrect=incorrect,
            skipped=skipped,
            total=total,
            time_used=time_used,
            answers=answer_details,
            warnings=warnings
        )
        
        result.save()
        
        # Удаляем сессию
        Session.delete_by_student(student.last_name, student.first_name)
        
        print(f'📊 Результат сохранён: {student.last_name} {student.first_name} - {score}%')
        
        # Возвращаем студенту только его результат (без правильных ответов)
        return jsonify({
            'success': True,
            'result': {
                'id': result.id,
                'score': score,
                'correct': correct,
                'incorrect': incorrect,
                'skipped': skipped,
                'total': total,
                'warnings': warnings,
                'warningPenalty': warning_penalty
            }
        })
    except Exception as e:
        print(f'Ошибка сохранения результата: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


# --- SESSIONS API ---

@app.route('/api/sessions', methods=['GET'])
@require_auth
def get_sessions():
    """Получить активные сессии (требует авторизации)"""
    try:
        sessions = Session.find_active()
        sessions_data = [s.to_dict() for s in sessions]
        return jsonify({'success': True, 'sessions': sessions_data})
    except Exception as e:
        print(f'Ошибка получения сессий: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sessions', methods=['POST'])
def create_session():
    """Создать сессию"""
    try:
        data = request.get_json() or {}
        
        student_data = data.get('student', {})
        student = SessionStudent(
            last_name=student_data.get('lastName', ''),
            first_name=student_data.get('firstName', ''),
            group_name=student_data.get('groupName', '')
        )
        
        session = Session(
            id=f'session_{int(time.time() * 1000)}_{secrets.token_hex(4)}',
            student=student,
            test_id=data.get('testId'),
            time_remaining=data.get('timeRemaining', 900),
            total_time=data.get('timeRemaining', 900),
            total_questions=data.get('totalQuestions', 0),
            status='active'
        )
        
        session.save()
        
        return jsonify({'success': True, 'sessionId': session.id})
    except Exception as e:
        print(f'Ошибка создания сессии: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sessions/<session_id>', methods=['PUT'])
def update_session(session_id):
    """Обновить сессию (heartbeat)"""
    try:
        data = request.get_json() or {}
        
        session = Session.objects(id=session_id).first()
        if not session:
            return jsonify({'success': False, 'error': 'Сессия не найдена'}), 404
        
        session.update_heartbeat(
            time_remaining=data.get('timeRemaining'),
            current_question=data.get('currentQuestion'),
            answers_count=data.get('answersCount'),
            warnings=data.get('warnings'),
            status=data.get('status')
        )
        
        return jsonify({'success': True})
    except Exception as e:
        print(f'Ошибка обновления сессии: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Удалить сессию"""
    try:
        Session.objects(id=session_id).delete()
        return jsonify({'success': True})
    except Exception as e:
        print(f'Ошибка удаления сессии: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== SERVE FRONTEND ==========

@app.route('/')
def index():
    """Главная страница"""
    return send_from_directory('public', 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Отдаёт статические файлы из папки public"""
    if os.path.exists(os.path.join('public', path)):
        return send_from_directory('public', path)
    return send_from_directory('public', 'index.html')


# ========== ERROR HANDLING ==========

@app.errorhandler(404)
def not_found(e):
    """Обработчик 404 ошибки"""
    return jsonify({'success': False, 'error': 'Не найдено'}), 404


@app.errorhandler(500)
def server_error(e):
    """Обработчик 500 ошибки"""
    print(f'Ошибка сервера: {e}')
    return jsonify({'success': False, 'error': 'Внутренняя ошибка сервера'}), 500


# ========== MAIN ==========

if __name__ == '__main__':
    # Проверяем обязательные переменные окружения
    errors = config.validate()
    for error in errors:
        print(error)
    
    critical_errors = [e for e in errors if e.startswith('❌')]
    if critical_errors:
        exit(1)
    
    # Подключаемся к MongoDB
    connect_mongodb()
    
    # Запускаем сервер
    print(f'🚀 SmartGrade сервер запущен на порту {config.PORT}')
    print(f'📡 API доступен по адресу: http://localhost:{config.PORT}/api')
    print(f'🌐 Фронтенд: http://localhost:{config.PORT}')
    
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )