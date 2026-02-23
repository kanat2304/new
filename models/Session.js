const mongoose = require('mongoose');

const SessionStudentSchema = new mongoose.Schema({
    lastName: String,
    firstName: String,
    groupName: String
}, { _id: false });

const SessionSchema = new mongoose.Schema({
    id: {
        type: String,
        required: true,
        unique: true
    },
    student: {
        type: SessionStudentSchema,
        required: true
    },
    testId: {
        type: String,
        required: true,
        ref: 'Test'
    },
    startTime: {
        type: Date,
        default: Date.now
    },
    timeRemaining: {
        type: Number,
        default: 900
    },
    totalTime: {
        type: Number,
        default: 900
    },
    currentQuestion: {
        type: Number,
        default: 0
    },
    totalQuestions: {
        type: Number,
        default: 0
    },
    answersCount: {
        type: Number,
        default: 0
    },
    warnings: {
        type: Number,
        default: 0
    },
    status: {
        type: String,
        enum: ['active', 'completed', 'blocked'],
        default: 'active'
    },
    lastUpdate: {
        type: Date,
        default: Date.now
    }
});

// TTL индекс - автоматически удаляет неактивные сессии через 10 минут
SessionSchema.index({ lastUpdate: 1 }, { expireAfterSeconds: 600 });

// Индекс для быстрого поиска активных сессий
SessionSchema.index({ testId: 1, status: 1 });

module.exports = mongoose.model('Session', SessionSchema);
