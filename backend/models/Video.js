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
  publishDate: Date,
  isActive: { type: Boolean, default: true },
  tags: [{ type: String }],
  createdAt: { type: Date, default: Date.now },
  updatedAt: { type: Date, default: Date.now },
});

const Video = mongoose.model('Video', videoSchema);

module.exports = Video;