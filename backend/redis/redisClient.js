const { createClient } = require('redis');

const redisClient = createClient();

redisClient.on('error', (err) => console.error('❌ Redis error:', err.message));
redisClient.on('connect', () => console.log('✅ Redis connected'));
redisClient.on('reconnecting', () => console.log('♻️ Reconnecting Redis...'));

(async () => {
  try {
    await redisClient.connect();
  } catch (err) {
    console.error('⚠️ Redis startup failed:', err.message);
  }
})();

module.exports = redisClient;
