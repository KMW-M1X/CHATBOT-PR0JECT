
require('dotenv').config();
const cloudinary = require('cloudinary').v2;



// Set up Cloudinary configuration
const connectCloudinary = () => {
  cloudinary.config({
    cloud_name: process.env.VITE_CLOUDINARY_CLOUD_NAME,
    api_key: process.env.CLOUDINARY_API_KEY,
    api_secret: process.env.CLOUDINARY_API_SECRET,
  });
  console.log('Cloudinary Connected');
};

module.exports = { cloudinary, connectCloudinary };
