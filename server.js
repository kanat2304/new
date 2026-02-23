require('dotenv').config();
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const path = require('path');

const Test = require('./models/Test');
const Result = require('./models/Result');
const Session = require('./models/Session');

const app = express();
const PORT = process.env.PORT || 3000;

// ========== MIDDLEWARE ==========
app.use(cors());
app.use(express.json({ limit: '50mb' })); // Увеличенный лимит для больших тестов
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Статические файлы (HTML, CSS, JS)
app.use(express.static(path.join(__dirname)));

// ========== MONGODB CONNECTION ==========
const MONGODB_URI = process.env.MONGODB_URI;

if (!MONGODB_URI) {
    console.error('❌ Ошибка: MONGODB_URI не определён в .env файле');
    process.exit(1);
}

mongoose.connect(MONGODB_URI)
    .then(() => console.log('✅ MongoDB подключена успешно'))
    .catch(err => {
        console.error('❌ Ошибка подключения MongoDB:', err.message);
        process.exit(1);
    });

// ========== API ROUTES ==========

// --- HEALTH CHECK ---
app.get('/api/health', (req, res) => {
    res.json({ 
        status: 'ok', 
        message: 'SmartGrade API работает',
        timestamp: new Date().toISOString()
    });
});

// --- TESTS API ---

// Получить все тесты
app.get('/api/tests', async (req, res) => {
    try {
        const tests = await Test.find({ isActive: true })
            .sort({ createdAt: -1 })
            .select('-questions.correct'); // Скрываем правильные ответы
        
        res.json({ success: true, tests });
    } catch (error) {
        console.error('Ошибка получения тестов:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// Получить тест по ID
app.get('/api/tests/:id', async (req, res) => {
    try {
        const test = await Test.findOne({ id: req.params.id });
        
        if (!test) {
            return res.status(404).json({ success: false, error: 'Тест не найден' });
        }
        
        res.json({ success: true, test });
    } catch (error) {
        console.error('Ошибка получения теста:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// Создать новый тест
app.post('/api/tests', async (req, res) => {
    try {
        const { id, name, description, questions, selectedCount, timeLimit, mode } = req.body;
        
        // Проверяем, существует ли тест с таким ID
        const existingTest = await Test.findOne({ id });
        if (existingTest) {
            return res.status(400).json({ 
                success: false, 
                error: 'Тест с таким ID уже существует' 
            });
        }
        
        const test = new Test({
            id: id || 'test_' + Date.now(),
            name: name || 'Тест от ' + new Date().toLocaleDateString('ru-RU'),
            description: description || '',
            questions: questions || [],
            selectedCount: selectedCount || questions?.length || 20,
            timeLimit: timeLimit || 900,
            mode: mode || 'lite'
        });
        
        await test.save();
        
        console.log(`✅ Тест создан: ${test.name} (${test.id})`);
        
        res.json({ 
            success: true, 
            test: {
                id: test.id,
                name: test.name,
                questionCount: test.questions.length,
                timeLimit: test.timeLimit,
                mode: test.mode
            }
        });
    } catch (error) {
        console.error('Ошибка создания теста:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// Удалить тест
app.delete('/api/tests/:id', async (req, res) => {
    try {
        const test = await Test.findOneAndDelete({ id: req.params.id });
        
        if (!test) {
            return res.status(404).json({ success: false, error: 'Тест не найден' });
        }
        
        // Также удаляем связанные результаты
        await Result.deleteMany({ testId: req.params.id });
        
        console.log(`🗑️ Тест удалён: ${test.name} (${test.id})`);
        
        res.json({ success: true, message: 'Тест удалён' });
    } catch (error) {
        console.error('Ошибка удаления теста:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// --- RESULTS API ---

// Получить все результаты
app.get('/api/results', async (req, res) => {
    try {
        const { testId, group } = req.query;
        
        let query = {};
        if (testId) query.testId = testId;
        if (group) query['student.groupName'] = group;
        
        const results = await Result.find(query)
            .sort({ date: -1 })
            .limit(500);
        
        res.json({ success: true, results });
    } catch (error) {
        console.error('Ошибка получения результатов:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// Получить статистику
app.get('/api/results/stats', async (req, res) => {
    try {
        const stats = await Result.aggregate([
            {
                $group: {
                    _id: null,
                    totalStudents: { $sum: 1 },
                    avgScore: { $avg: '$score' },
                    totalViolations: { $sum: '$warnings' },
                    totalCorrect: { $sum: '$correct' },
                    totalIncorrect: { $sum: '$incorrect' }
                }
            }
        ]);
        
        const uniqueTests = await Result.distinct('testId');
        
        const result = stats[0] || {
            totalStudents: 0,
            avgScore: 0,
            totalViolations: 0
        };
        
        res.json({
            success: true,
            stats: {
                totalStudents: result.totalStudents,
                avgScore: Math.round(result.avgScore || 0),
                totalViolations: result.totalViolations,
                totalTests: uniqueTests.length
            }
        });
    } catch (error) {
        console.error('Ошибка получения статистики:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// Сохранить результат
app.post('/api/results', async (req, res) => {
    try {
        const { student, testId, testName, score, correct, incorrect, skipped, total, timeUsed, answers, warnings } = req.body;
        
        const result = new Result({
            id: 'result_' + Date.now(),
            student,
            testId,
            testName: testName || 'Неизвестный тест',
            score,
            correct,
            incorrect,
            skipped,
            total,
            timeUsed,
            answers: answers || [],
            warnings: warnings || 0
        });
        
        await result.save();
        
        // Удаляем сессию
        await Session.deleteMany({ 'student.lastName': student.lastName, 'student.firstName': student.firstName });
        
        console.log(`📊 Результат сохранён: ${student.lastName} ${student.firstName} - ${score}%`);
        
        res.json({ success: true, result: { id: result.id, score: result.score } });
    } catch (error) {
        console.error('Ошибка сохранения результата:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// --- SESSIONS API ---

// Получить активные сессии
app.get('/api/sessions', async (req, res) => {
    try {
        // Получаем сессии, обновлённые за последние 60 секунд
        const oneMinuteAgo = new Date(Date.now() - 60000);
        
        const sessions = await Session.find({
            status: 'active',
            lastUpdate: { $gte: oneMinuteAgo }
        }).sort({ startTime: -1 });
        
        res.json({ success: true, sessions });
    } catch (error) {
        console.error('Ошибка получения сессий:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// Создать сессию
app.post('/api/sessions', async (req, res) => {
    try {
        const { student, testId, timeRemaining, totalQuestions } = req.body;
        
        const session = new Session({
            id: 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
            student,
            testId,
            timeRemaining,
            totalTime: timeRemaining,
            totalQuestions,
            status: 'active'
        });
        
        await session.save();
        
        res.json({ success: true, sessionId: session.id });
    } catch (error) {
        console.error('Ошибка создания сессии:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// Обновить сессию (heartbeat)
app.put('/api/sessions/:id', async (req, res) => {
    try {
        const { timeRemaining, currentQuestion, answersCount, warnings, status } = req.body;
        
        const session = await Session.findOneAndUpdate(
            { id: req.params.id },
            {
                timeRemaining,
                currentQuestion,
                answersCount,
                warnings,
                status,
                lastUpdate: new Date()
            },
            { new: true }
        );
        
        if (!session) {
            return res.status(404).json({ success: false, error: 'Сессия не найдена' });
        }
        
        res.json({ success: true });
    } catch (error) {
        console.error('Ошибка обновления сессии:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// Удалить сессию
app.delete('/api/sessions/:id', async (req, res) => {
    try {
        await Session.findOneAndDelete({ id: req.params.id });
        res.json({ success: true });
    } catch (error) {
        console.error('Ошибка удаления сессии:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// ========== SERVE FRONTEND ==========
// Главная страница
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// Все остальные HTML файлы
app.get('/:page', (req, res, next) => {
    const page = req.params.page;
    if (page.endsWith('.html')) {
        res.sendFile(path.join(__dirname, page));
    } else {
        next();
    }
});

// ========== ERROR HANDLING ==========
app.use((err, req, res, next) => {
    console.error('Ошибка сервера:', err);
    res.status(500).json({ 
        success: false, 
        error: 'Внутренняя ошибка сервера' 
    });
});

// ========== START SERVER ==========
app.listen(PORT, () => {
    console.log(`🚀 SmartGrade сервер запущен на порту ${PORT}`);
    console.log(`📡 API доступен по адресу: http://localhost:${PORT}/api`);
    console.log(`🌐 Фронтенд: http://localhost:${PORT}`);
});
