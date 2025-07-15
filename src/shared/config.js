module.exports = {
    DISK_MOUNT_PATH: process.env.DISK_MOUNT_PATH || './tmp', // ローカル実行時はtmpフォルダ
    INVIDIOUS_INSTANCE_URL: 'https://invidious.nikkosphere.com',
    JOB_CHANNEL: 'video-jobs', // RedisのPub/Subチャンネル名
    JOB_KEY_PREFIX: 'job:', // Redisのジョブ状態キー
};
