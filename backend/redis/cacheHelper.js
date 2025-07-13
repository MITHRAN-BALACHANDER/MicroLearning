const redis = require('./redisClient');

async function getWithCache(key, fetchFunction, ttlInSeconds = 3600) {
  try {
    const cached = await redis.get(key);
    if (cached) {
      return JSON.parse(cached);
    }
  } catch (err) {
    console.warn('⚠️ Redis read failed:', err.message);
  }

  // Fallback to fetching from source
  const data = await fetchFunction();

  try {
    await redis.set(key, JSON.stringify(data), { EX: ttlInSeconds });
  } catch (err) {
    console.warn('⚠️ Redis write failed:', err.message);
  }

  return data;
}

module.exports = { getWithCache };
