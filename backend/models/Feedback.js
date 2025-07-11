const mongoose = require('mongoose');

const feedbackSchema = new mongoose.Schema({
  userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  comment: { type: String, trim: true },
}, { timestamps: true });

module.exports = mongoose.model('Feedback', feedbackSchema);
