const mongoose = require('mongoose');
const dotenv = require('dotenv');
const path = require('path');
const Video = require('../models/Video');

dotenv.config({ path: path.resolve(__dirname, '../.env') });
mongoose.connect(process.env.MONGO_URI);

const video = new Video({
  title: 'Sample Video',
  description: 'This is a sample video description.',
  videoUrl: 'http://example.com/video.mp4',
  thumbnailUrl: 'http://example.com/thumbnail.jpg',
  categoryId: '686ba0f9c8c35fc3c27e6f39',
  uploadedBy: '6866050cb072e11c7005abbf',
  views: 100,
  likes: 50,
  averageRating: 4.5,
  ratingsCount: 10,
  isPublished: true,
  publishDate: new Date(),
  isActive: true,
  tags: ['sample', 'video'],
});

video.save()
  .then(() => {
    console.log('Video seeded successfully');
    mongoose.connection.close();
  })
  .catch(err => {
    console.error('Error seeding video:', err);
    mongoose.connection.close();
  });
