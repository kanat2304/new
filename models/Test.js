const mongoose = require('mongoose');

const QuestionSchema = new mongoose.Schema({
    id: {
        type: Number,
        required: true
    },
    text: {
        type: String,
        required: true
    },
    options: [{
        type: String,
        required: true
    }],
    correct: {
        type: Number,
        required: true
    }
}, { _id: false });

const TestSchema = new mongoose.Schema({
    id: {
        type: String,
        required: true,
        unique: true
    },
    name: {
        type: String,
        required: true,
        default: 'Тест без названия'
    },
    description: {
        type: String,
        default: ''
    },
    questions: [QuestionSchema],
    selectedCount: {
        type: Number,
        default: 20
    },
    timeLimit: {
        type: Number,
        default: 900 // 15 минут в секундах
    },
    mode: {
        type: String,
        enum: ['lite', 'hard'],
        default: 'lite'
    },
    createdAt: {
        type: Date,
        default: Date.now
    },
    createdBy: {
        type: String,
        default: 'teacher'
    },
    isActive: {
        type: Boolean,
        default: true
    }
});

// Индекс для быстрого поиска по ID
TestSchema.index({ id: 1 });

module.exports = mongoose.model('Test', TestSchema);
