const { createClient } = require('redis');

const redisClient = createClient({
  /*
    username: 'default',
    password: 'mFJrtq88Rs5Hg6MohUDhEBCNiOv98BwJ',
    socket: {
        host: 'redis-13260.c98.us-east-1-4.ec2.redns.redis-cloud.com',
        port: 13260
    } */
});

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
