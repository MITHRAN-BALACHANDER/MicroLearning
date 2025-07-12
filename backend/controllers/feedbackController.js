const Feedback = require('../models/Feedback');

exports.createFeedback = async (req, res) => {
  try {
    const { comment } = req.body;
    const feedback = new Feedback({
      userId: req.user.id,
      comment
    });
    await feedback.save();
    res.status(201).json({ message: 'Feedback created successfully', feedback });
  } catch (error) {
    res.status(500).json({ message: 'Error creating feedback', error: error.message });
  }
}

exports.getFeedbacks = async (req, res) => {
  try {
    const feedbacks = await Feedback.find().populate('userId', 'user email');
    res.status(200).json(feedbacks);
  } catch (error) {
    res.status(500).json({ message: 'Error fetching feedbacks', error: error.message });
  }
}