const mongoose = require('mongoose');

const ratingSchema = new mongoose.Schema({
    userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
    videoId: { type: mongoose.Schema.Types.ObjectId, ref: 'Video', required: true },
    rating: { type: Number, required: true, min: 1, max: 5 },
    ratedAt: { type: Date, default: Date.now },
});

const Rating = mongoose.model('Rating', ratingSchema);

module.exports = Rating;