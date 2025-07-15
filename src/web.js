const express = require('express');
const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');
const { redis, getJob } = require('./shared/redis');
const { DISK_MOUNT_PATH, JOB_CHANNEL } = require('./shared/config');

const app = express();
app.use(express.json());

// 1. ジョブ作成API
app.post('/api/generate', async (req, res) => {
    const { v: videoId } = req.query;
    if (!videoId || !/^[a-zA-Z0-9_-]{11}$/.test(videoId)) {
        return res.status(400).send({ error: 'Valid "v" parameter is required.' });
    }

    const jobId = uuidv4();
    const job = {
        jobId,
        videoId,
        status: 'queued',
        createdAt: new Date().toISOString(),
    };
    await redis.set(`job:${jobId}`, JSON.stringify(job));
    await redis.publish(JOB_CHANNEL, JSON.stringify(job)); // Workerに通知

    res.status(202).json({ jobId }); // 202 Acceptedを返すのがセオリー
});

// 2. 状態確認API
app.get('/api/status/:jobId', async (req, res) => {
    const job = await getJob(req.params.jobId);
    if (!job) {
        return res.status(404).json({ error: 'Job not found.' });
    }
    res.status(200).json(job);
});

// 3. ダウンロードAPI
app.get('/api/download/:jobId', async (req, res) => {
    const job = await getJob(req.params.jobId);
    if (job?.status !== 'completed' || !job.outputPath) {
        return res.status(404).send({ error: 'File is not ready or does not exist.' });
    }
    const filePath = path.join(DISK_MOUNT_PATH, job.outputPath);
    if (!fs.existsSync(filePath)) {
        return res.status(404).send({ error: 'File not found on disk.' });
    }
    res.download(filePath, job.filename, (err) => {
        if (!err) {
            // ダウンロード成功後にファイルを削除してディスクを節約
            fs.unlink(filePath, () => {});
        }
    });
});

app.get('/health', (req, res) => res.status(200).send('OK'));

app.listen(3000, () => console.log('Web service started.'));
