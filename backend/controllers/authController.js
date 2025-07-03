const Admin = require('../models/Admin');
const generateToken = require('../utils/generateToken');

exports.login = async (req, res) => {
  const { email, password } = req.body;
  try {
    const user = await Admin.findOne({ email });
    if (!user || !(await user.matchPassword(password))) {
      return res.status(401).json({ message: 'Invalid credentials' });
    }

    const token = generateToken(user._id);
    res.json({ token, user: { name: user.name, role: user.role } });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};
