const User = require('../models/User');
const Category = require('../models/Category');
const Video = require('../models/Video');
const Rating = require('../models/Rating');
const Feedback = require('../models/Feedback');
const mongoose = require('mongoose');

// ============ User Management ============

// Get all users with pagination and search
exports.getAllUsers = async (req, res) => {
  try {
    const { page = 1, limit = 10, search = '' } = req.query;
    const skip = (page - 1) * limit;

    const query = search
      ? {
          $or: [
            { name: { $regex: search, $options: 'i' } },
            { email: { $regex: search, $options: 'i' } },
            { phone: { $regex: search, $options: 'i' } },
          ],
        }
      : {};

    const users = await User.find(query)
      .select('-password')
      .skip(skip)
      .limit(parseInt(limit))
      .sort({ createdAt: -1 });

    const total = await User.countDocuments(query);

    res.json({
      users,
      pagination: {
        total,
        page: parseInt(page),
        limit: parseInt(limit),
        pages: Math.ceil(total / limit),
      },
    });
  } catch (err) {
    res.status(500).json({ message: 'Server error', error: err.message });
  }
};

// Update user
exports.updateUser = async (req, res) => {
  try {
    const { id } = req.params;
    const { name, email, phone } = req.body;

    const user = await User.findByIdAndUpdate(
      id,
      { name, email, phone },
      { new: true, runValidators: true }
    ).select('-password');

    if (!user) {
      return res.status(404).json({ message: 'User not found' });
    }

    res.json({ message: 'User updated successfully', user });
  } catch (err) {
    res.status(500).json({ message: 'Server error', error: err.message });
  }
};

// Delete user
exports.deleteUser = async (req, res) => {
  try {
    const { id } = req.params;
    const user = await User.findByIdAndDelete(id);

    if (!user) {
      return res.status(404).json({ message: 'User not found' });
    }

    res.json({ message: 'User deleted successfully' });
  } catch (err) {
    res.status(500).json({ message: 'Server error', error: err.message });
  }
};

// Get user statistics
exports.getUserStats = async (req, res) => {
  try {
    const totalUsers = await User.countDocuments();
    const recentUsers = await User.countDocuments({
      createdAt: { $gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) },
    });

    res.json({
      totalUsers,
      recentUsers,
    });
  } catch (err) {
    res.status(500).json({ message: 'Server error', error: err.message });
  }
};

// ============ Analytics ============

// Get dashboard analytics
exports.getDashboardAnalytics = async (req, res) => {
  try {
    const totalUsers = await User.countDocuments();
    const totalCategories = await Category.countDocuments();
    const totalVideos = await Video.countDocuments();
    const totalRatings = await Rating.countDocuments();

    // Get average rating
    const avgRatingResult = await Rating.aggregate([
      {
        $group: {
          _id: null,
          avgRating: { $avg: '$rating' },
        },
      },
    ]);
    const avgRating = avgRatingResult.length > 0 ? avgRatingResult[0].avgRating : 0;

    // Get recent users (last 30 days)
    const recentUsers = await User.countDocuments({
      createdAt: { $gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) },
    });

    // Get recent videos (last 30 days)
    const recentVideos = await Video.countDocuments({
      createdAt: { $gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) },
    });

    // Get video views (assuming you have a views field)
    const totalViewsResult = await Video.aggregate([
      {
        $group: {
          _id: null,
          totalViews: { $sum: '$views' },
        },
      },
    ]);
    const totalViews = totalViewsResult.length > 0 ? totalViewsResult[0].totalViews : 0;

    res.json({
      totalUsers,
      totalCategories,
      totalVideos,
      totalRatings,
      avgRating: avgRating.toFixed(2),
      recentUsers,
      recentVideos,
      totalViews,
    });
  } catch (err) {
    res.status(500).json({ message: 'Server error', error: err.message });
  }
};

// Get video analytics
exports.getVideoAnalytics = async (req, res) => {
  try {
    // Top rated videos
    const topRatedVideos = await Rating.aggregate([
      {
        $group: {
          _id: '$videoId',
          avgRating: { $avg: '$rating' },
          totalRatings: { $sum: 1 },
        },
      },
      { $sort: { avgRating: -1 } },
      { $limit: 10 },
      {
        $lookup: {
          from: 'videos',
          localField: '_id',
          foreignField: '_id',
          as: 'video',
        },
      },
      { $unwind: '$video' },
      {
        $project: {
          videoId: '$_id',
          title: '$video.title',
          avgRating: 1,
          totalRatings: 1,
        },
      },
    ]);

    // Videos by category
    const videosByCategory = await Video.aggregate([
      {
        $lookup: {
          from: 'categories',
          localField: 'categoryId',
          foreignField: '_id',
          as: 'category',
        },
      },
      { $unwind: { path: '$category', preserveNullAndEmptyArrays: true } },
      {
        $group: {
          _id: '$categoryId',
          categoryName: { $first: '$category.name' },
          count: { $sum: 1 },
        },
      },
      { $sort: { count: -1 } },
    ]);

    res.json({
      topRatedVideos,
      videosByCategory,
    });
  } catch (err) {
    res.status(500).json({ message: 'Server error', error: err.message });
  }
};

// Get user engagement analytics
exports.getUserEngagement = async (req, res) => {
  try {
    // User registration trend (last 12 months)
    const userTrend = await User.aggregate([
      {
        $match: {
          createdAt: { $gte: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000) },
        },
      },
      {
        $group: {
          _id: {
            year: { $year: '$createdAt' },
            month: { $month: '$createdAt' },
          },
          count: { $sum: 1 },
        },
      },
      { $sort: { '_id.year': 1, '_id.month': 1 } },
    ]);

    // Rating distribution
    const ratingDistribution = await Rating.aggregate([
      {
        $group: {
          _id: '$rating',
          count: { $sum: 1 },
        },
      },
      { $sort: { _id: 1 } },
    ]);

    res.json({
      userTrend,
      ratingDistribution,
    });
  } catch (err) {
    res.status(500).json({ message: 'Server error', error: err.message });
  }
};

// ============ Category & Video Management ============

// Get all categories with video counts
exports.getCategoriesWithStats = async (req, res) => {
  try {
    const categories = await Category.aggregate([
      {
        $lookup: {
          from: 'videos',
          localField: '_id',
          foreignField: 'categoryId',
          as: 'videos',
        },
      },
      {
        $project: {
          name: 1,
          description: 1,
          image: 1,
          parentCategory: 1,
          createdAt: 1,
          videoCount: { $size: '$videos' },
        },
      },
      { $sort: { createdAt: -1 } },
    ]);

    res.json(categories);
  } catch (err) {
    res.status(500).json({ message: 'Server error', error: err.message });
  }
};

// Get all videos with stats
exports.getVideosWithStats = async (req, res) => {
  try {
    const { page = 1, limit = 10, categoryId, search = '' } = req.query;
    const skip = (page - 1) * limit;

    const matchQuery = {};
    if (categoryId && mongoose.Types.ObjectId.isValid(categoryId)) {
      matchQuery.categoryId = new mongoose.Types.ObjectId(categoryId);
    }
    if (search) {
      matchQuery.title = { $regex: search, $options: 'i' };
    }

    const videos = await Video.aggregate([
      { $match: matchQuery },
      {
        $lookup: {
          from: 'ratings',
          localField: '_id',
          foreignField: 'videoId',
          as: 'ratings',
        },
      },
      {
        $lookup: {
          from: 'categories',
          localField: 'categoryId',
          foreignField: '_id',
          as: 'category',
        },
      },
      {
        $project: {
          title: 1,
          description: 1,
          videoUrl: 1,
          categoryId: 1,
          categoryName: { $arrayElemAt: ['$category.name', 0] },
          createdAt: 1,
          views: 1,
          ratingCount: { $size: '$ratings' },
          avgRating: { $avg: '$ratings.rating' },
        },
      },
      { $sort: { createdAt: -1 } },
      { $skip: skip },
      { $limit: parseInt(limit) },
    ]);

    const total = await Video.countDocuments(matchQuery);

    res.json({
      videos,
      pagination: {
        total,
        page: parseInt(page),
        limit: parseInt(limit),
        pages: Math.ceil(total / limit),
      },
    });
  } catch (err) {
    res.status(500).json({ message: 'Server error', error: err.message });
  }
};

// Delete video
exports.deleteVideo = async (req, res) => {
  try {
    const { id } = req.params;
    const video = await Video.findByIdAndDelete(id);

    if (!video) {
      return res.status(404).json({ message: 'Video not found' });
    }

    // Also delete associated ratings
    await Rating.deleteMany({ videoId: id });

    res.json({ message: 'Video deleted successfully' });
  } catch (err) {
    res.status(500).json({ message: 'Server error', error: err.message });
  }
};

// Delete category
exports.deleteCategory = async (req, res) => {
  try {
    const { id } = req.params;

    // Check if category has videos
    const videoCount = await Video.countDocuments({ categoryId: id });
    if (videoCount > 0) {
      return res.status(400).json({
        message: 'Cannot delete category with existing videos',
        videoCount,
      });
    }

    const category = await Category.findByIdAndDelete(id);

    if (!category) {
      return res.status(404).json({ message: 'Category not found' });
    }

    res.json({ message: 'Category deleted successfully' });
  } catch (err) {
    res.status(500).json({ message: 'Server error', error: err.message });
  }
};

// Get feedback
exports.getAllFeedback = async (req, res) => {
  try {
    const { page = 1, limit = 10 } = req.query;
    const skip = (page - 1) * limit;

    const feedback = await Feedback.find()
      .populate('userId', 'name email')
      .skip(skip)
      .limit(parseInt(limit))
      .sort({ createdAt: -1 });

    const total = await Feedback.countDocuments();

    res.json({
      feedback,
      pagination: {
        total,
        page: parseInt(page),
        limit: parseInt(limit),
        pages: Math.ceil(total / limit),
      },
    });
  } catch (err) {
    res.status(500).json({ message: 'Server error', error: err.message });
  }
};
