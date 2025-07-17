from flask import Flask, request, jsonify
from pytube import YouTube
import logging

# Flaskアプリケーションのインスタンスを作成
app = Flask(__name__)

# ログ設定
logging.basicConfig(level=logging.INFO)

@app.route('/', methods=['GET'])
def get_stream_url():
    # URLのクエリパラメータから 'i' (YouTube動画ID) を取得
    video_id = request.args.get('i')

    # 'i' パラメータが存在しない場合はエラーメッセージを返す
    if not video_id:
        return jsonify({"error": "ビデオIDが指定されていません。'?i=<YouTubeのビデオID>' の形式で指定してください。"}), 400

    try:
        # YouTube動画のURLを構築
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
        app.logger.info(f"動画URLを処理中: {youtube_url}")

        # pytubeでYouTubeオブジェクトを作成
        yt = YouTube(youtube_url)

        # 利用可能なストリームの中から、プログレッシブ（映像と音声が一体）で
        # 解像度が最も高いものを取得
        stream = yt.streams.filter(progressive=True, file_extension='mp4').get_highest_resolution()

        # ストリームが見つかった場合は、そのURLをJSON形式で返す
        if stream:
            app.logger.info(f"ストリームURLが見つかりました: {stream.url}")
            return jsonify({
                "video_id": video_id,
                "title": yt.title,
                "stream_url": stream.url
            })
        # ストリームが見つからない場合はエラーメッセージを返す
        else:
            app.logger.warning("利用可能なストリームが見つかりませんでした。")
            return jsonify({"error": "利用可能なストリームが見つかりませんでした。"}), 404

    except Exception as e:
        # その他のエラーが発生した場合
        app.logger.error(f"エラーが発生しました: {e}")
        return jsonify({"error": f"エラーが発生しました: {str(e)}"}), 500

if __name__ == '__main__':
    # この部分はRailwayでは使用されませんが、念のため残しておきます
    app.run(host='0.0.0.0', port=8080)
