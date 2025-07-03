const Admin = require('../models/Admin');
const User = require('../models/User');
const generateToken = require('../utils/generateToken');

exports.login = async (req, res) => {
  const { email, password } = req.body;

  try {
    // Check in Admin collection
    let user = await Admin.findOne({ email });
    let role = 'admin';

    if (!user) {
      // If not admin, check in User
      user = await User.findOne({ email });
      role = 'user';
    }

    if (!user) {
      return res.status(401).json({ message: 'Invalid email or password' });
    }

    const isMatch = await user.matchPassword(password);
    if (!isMatch) {
      return res.status(401).json({ message: 'Invalid email or password' });
    }

    const token = generateToken({ id: user._id, role });

    res.json({
      token,
      user: {
        id: user._id,
        name: user.name,
        email: user.email,
        role,
      },
    });
  } catch (err) {
    res.status(500).json({ message: 'Server error', error: err.message });
  }
};
