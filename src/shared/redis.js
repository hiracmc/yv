const Redis = require('ioredis');
const { JOB_KEY_PREFIX } = require('./config');

const redis = new Redis(process.env.REDIS_URL);
const sub = new Redis(process.env.REDIS_URL); // Subscribe専用クライアント

async function getJob(jobId) {
    const jobJson = await redis.get(`${JOB_KEY_PREFIX}${jobId}`);
    return jobJson ? JSON.parse(jobJson) : null;
}

async function setJob(jobId, jobData) {
    await redis.set(`${JOB_KEY_PREFIX}${jobId}`, JSON.stringify(jobData));
}

async function updateJobStatus(jobId, status, data = {}) {
    const job = await getJob(jobId);
    if (job) {
        job.status = status;
        job.updatedAt = new Date().toISOString();
        Object.assign(job, data);
        await setJob(jobId, job);
    }
}

module.exports = { redis, sub, getJob, setJob, updateJobStatus };
