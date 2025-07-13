const jwt = require('jsonwebtoken');

// Middleware to protect routes
function protect(req, res, next) {
  const token = req.cookies.token
  if (!token) return res.status(401).json({ message: 'Not authorized, no token' });

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = decoded;
    next();
  } catch (err) {
    res.status(401).json({ message: 'Not authorized, token failed' });
  }
}

// Optional: Middleware for admin check
function admin(req, res, next) {
  if (req.user && req.user.role === 'admin') {
    next();
  } else {
    res.status(403).json({ message: 'Admin access required' });
  }
}

module.exports = { protect, admin };
