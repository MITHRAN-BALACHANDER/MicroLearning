const Rating = require('../models/Rating');
const Video = require('../models/Video');

// Create a new rating
exports.createRating = async (req, res) => {
    try {
        const { videoId, rating } = req.body;

        // Validate rating value
        if (rating < 1 || rating > 5) {
            return res.status(400).json({ message: 'Rating must be between 1 and 5' });
        }

        // Check if video exists
        const video = await Video.findById(videoId);
        if (!video) {
            return res.status(404).json({ message: 'Video not found' });
        }

        // Create new rating
        const newRating = new Rating({
            userId: req.user.id,
            videoId,
            rating
        });

        await newRating.save();

        // Update video's average rating and ratings count
        video.ratingsCount += 1;
        video.averageRating = ((video.averageRating * (video.ratingsCount - 1)) + rating) / video.ratingsCount;
        await video.save();

        res.status(201).json(newRating);
    } catch (error) {
        res.status(500).json({ message: 'Server error', error: error.message });
    }
};

// Get ratings for a video by user
exports.getRatings = async (req, res) => {
    try {
        // Find ratings for the specified video and user
        const ratings = await Rating.find({ videoId: req.params.videoId, userId: req.user.id });
        if (ratings.length === 0) {
            return res.status(404).json({ message: 'No ratings found for this video by this user' });
        }

        res.status(200).json(ratings);
    } catch (error) {
        res.status(500).json({ message: 'Server error', error: error.message });
    }
};


