const multer = require('multer');

const errorHandler = (err, req, res, next) => {
  // Handle Multer errors
  if (err instanceof multer.MulterError) {
    if (err.code === 'LIMIT_FILE_SIZE') {
      return res.status(400).json({ 
        message: 'File too large. Maximum size is 100MB' 
      });
    }
    
    if (err.code === 'LIMIT_UNEXPECTED_FILE') {
      return res.status(400).json({ 
        message: 'Unexpected field. Make sure the field name is "videoFile"' 
      });
    }
    
    return res.status(400).json({ 
      message: `Multer error: ${err.message}` 
    });
  }
  
  // Handle other errors
  if (err.message === 'Only video files are allowed!') {
    return res.status(400).json({ message: err.message });
  }
  
  // Default error handling
  console.error(err);
  res.status(500).json({ 
    message: 'Server error', 
    error: process.env.NODE_ENV === 'production' ? 'An unexpected error occurred' : err.message 
  });
};

module.exports = errorHandler;
