const mongoose = require("mongoose")

const dotenv = require('dotenv');
const path = require('path');

dotenv.config({ path: path.resolve(__dirname, '../.env') });
mongoose.connect(process.env.MONGO_URI);

const Rating = require('../models/Rating');
const ratings = [
  {
    userId: '6866050cb072e11c7005abbf',
    videoId: '686c9b0c3f76d196129c4499',
    rating: 5,
  },
];

Rating.insertMany(ratings)
  .then(() => {
    console.log("Ratings seeded successfully");
    mongoose.connection.close();
  })
  .catch((error) => {
    console.error("Error seeding ratings:", error);
  });


