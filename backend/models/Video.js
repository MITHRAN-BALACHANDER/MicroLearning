const mongoose = require('mongoose');

const videoSchema = new mongoose.Schema({
  title: { type: String, required: true },
  description: String,
  videoUrl: { type: String, required: true },
  thumbnailUrl: { type: String, required: true },
  categoryId: { type: mongoose.Schema.Types.ObjectId, ref: 'Category', required: true },
  uploadedBy: { type: mongoose.Schema.Types.ObjectId, ref: 'Admin', required: true },
  views: { type: Number, default: 0 },
  averageRating: { type: Number, default: 0 },
  ratingsCount: { type: Number, default: 0 },
  isPublished: { type: Boolean, default: false },
  tags: [{ type: String }],
}, { timestamps: true });

const Video = mongoose.model('Video', videoSchema);

module.exports = Video;