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

    console.log('Generated token:', token ? 'Token exists' : 'No token');
    console.log('Token length:', token?.length);

    res.cookie('token', token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'Strict',
      maxAge: 5 * 24 * 60 * 60 * 1000,  // 5 days
    });

    const responseData = {
      token,
      user: {
        id: user._id,
        name: user.name,
        email: user.email,
        role,
      },
    };

    console.log('Sending response:', JSON.stringify(responseData, null, 2));

    res.json(responseData);
  } catch (err) {
    res.status(500).json({ message: 'Server error', error: err.message });
  }
};

exports.logout = (req, res) => {
  res.clearCookie('token', {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'Strict',
  });
  res.json({ message: 'Logged out successfully' });
};