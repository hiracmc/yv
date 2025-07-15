const path = require('path');
const fs = require('fs/promises');
const https = require('https');
const ffmpeg = require('fluent-ffmpeg');
const { sub, updateJobStatus } = require('./shared/redis');
const { DISK_MOUNT_PATH, JOB_CHANNEL, INVIDIOUS_INSTANCE_URL } = require('./shared/config');

// ヘルパー：ファイルのダウンロード
async function download(url, dest) {
  return new Promise((resolve, reject) => {
    https.get(url, res => res.pipe(fs.createWriteStream(dest)).on('finish', resolve).on('error', reject));
  });
}

// メイン処理
async function processVideo(job) {
    const { jobId, videoId } = job;
    await updateJobStatus(jobId, 'processing');

    const tempDir = path.join(DISK_MOUNT_PATH, jobId);
    const finalName = `output-${videoId}.webm`;
    const outputPath = path.join(jobId, finalName); // ディスク上の相対パス

    try {
        await fs.mkdir(tempDir);
        const apiUrl = `${INVIDIOUS_INSTANCE_URL}/api/v1/videos/${videoId}`;
        const response = await fetch(apiUrl);
        const data = await response.json();

        const audioUrl = data.adaptiveFormats.find(f => f.type === 'audio/webm')?.url;
        const videoUrl = data.adaptiveFormats.find(f => f.type === 'video/webm')?.url;
        if (!audioUrl || !videoUrl) throw new Error('WebM streams not found.');

        const audioPath = path.join(tempDir, 'audio.webm');
        const videoPath = path.join(tempDir, 'video.webm');

        await Promise.all([download(audioUrl, audioPath), download(videoUrl, videoPath)]);
        
        await new Promise((resolve, reject) => {
            ffmpeg()
                .input(videoPath).input(audioPath)
                .outputOptions(['-c:v copy', '-c:a copy'])
                .save(path.join(DISK_MOUNT_PATH, outputPath))
                .on('end', resolve).on('error', reject);
        });

        const filename = `${data.title.replace(/[^a-zA-Z0-9]/g, '_')}.webm`;
        await updateJobStatus(jobId, 'completed', { outputPath, filename });

    } catch (error) {
        console.error(`[${jobId}] Error:`, error);
        await updateJobStatus(jobId, 'failed', { error: error.message });
    } finally {
        await fs.rm(tempDir, { recursive: true, force: true }).catch(() => {}); // 一時ファイルを削除
    }
}

// Workerの起動
(async () => {
    await sub.subscribe(JOB_CHANNEL);
    console.log('Worker is listening for jobs...');
    sub.on('message', (channel, message) => {
        if (channel === JOB_CHANNEL) {
            console.log('Received job:', message);
            processVideo(JSON.parse(message));
        }
    });
})();
