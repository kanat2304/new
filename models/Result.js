const mongoose = require('mongoose');

const StudentSchema = new mongoose.Schema({
    lastName: {
        type: String,
        required: true
    },
    firstName: {
        type: String,
        required: true
    },
    groupName: {
        type: String,
        required: true
    }
}, { _id: false });

const AnswerDetailSchema = new mongoose.Schema({
    questionId: Number,
    questionText: String,
    options: [String],
    correctAnswer: Number,
    studentAnswer: Number,
    isCorrect: Boolean,
    status: {
        type: String,
        enum: ['correct', 'incorrect', 'skipped']
    }
}, { _id: false });

const ResultSchema = new mongoose.Schema({
    id: {
        type: String,
        required: true,
        unique: true
    },
    student: {
        type: StudentSchema,
        required: true
    },
    testId: {
        type: String,
        required: true,
        ref: 'Test'
    },
    testName: {
        type: String,
        default: 'Неизвестный тест'
    },
    score: {
        type: Number,
        required: true,
        min: 0,
        max: 100
    },
    correct: {
        type: Number,
        default: 0
    },
    incorrect: {
        type: Number,
        default: 0
    },
    skipped: {
        type: Number,
        default: 0
    },
    total: {
        type: Number,
        required: true
    },
    timeUsed: {
        type: Number,
        default: 0 // в секундах
    },
    date: {
        type: Date,
        default: Date.now
    },
    answers: [AnswerDetailSchema],
    warnings: {
        type: Number,
        default: 0
    },
    completedAt: {
        type: Date,
        default: Date.now
    }
});

// Индексы для быстрого поиска
ResultSchema.index({ testId: 1 });
ResultSchema.index({ 'student.groupName': 1 });
ResultSchema.index({ date: -1 });

module.exports = mongoose.model('Result', ResultSchema);
