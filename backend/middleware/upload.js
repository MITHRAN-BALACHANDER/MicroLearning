const multer = require('multer');
const path = require('path');
const fs = require('fs');

// Define allowed file types
const fileFilter = (req, file, cb) => {
    // Accept video files only
    if (file.mimetype.startsWith('video/')) {
        cb(null, true);
    } else {
        cb(new Error('Only video files are allowed!'), false);
    }
};

const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        const uploadDir = path.join(__dirname, '../uploads');
        fs.mkdirSync(uploadDir, { recursive: true });
        cb(null, uploadDir);
    },
    filename: (req, file, cb) => {
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
        cb(null, uniqueSuffix + path.extname(file.originalname));
    }
});

// Set file size limits (e.g., 100MB)
const limits = {
    fileSize: 100 * 1024 * 1024 // 100MB in bytes
};

const upload = multer({
    storage,
    fileFilter,
    limits
});

module.exports = upload;