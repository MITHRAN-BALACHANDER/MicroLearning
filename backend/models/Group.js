const mongoose = require('mongoose');

const groupSchema = new mongoose.Schema({
    name: { type: String, required: true, unique: true },
    description: String,
    category: [{ type: mongoose.Schema.Types.ObjectId, ref: 'Category' }],
    members: [{ type: mongoose.Schema.Types.ObjectId, ref: 'User' }],
    isActive: { type: Boolean, default: true },
}, { timestamps: true }); 

const Group = mongoose.model('Group', groupSchema);

module.exports = Group;