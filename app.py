import os
from flask import Flask, request, jsonify
from pytube import YouTube

app = Flask(__name__)

@app.route('/')
def main():
    video_id = request.args.get('i')

    if not video_id:
        response = {
            "status": "error",
            "message": "URLに 'i' パラメータが見つかりませんでした。例: /?i=your_video_id"
        }
        return jsonify(response), 400

    try:
        print(f'動画ID: {video_id} の処理を開始します。')
        yt = YouTube(f'https://www.youtube.com/watch?v={video_id}')
        stream = yt.streams.get_highest_resolution()
        
        if stream and stream.url:
            response = {
                "status": "success",
                "video_id": video_id,
                "stream_url": stream.url
            }
            return jsonify(response), 200
        else:
            response = {
                "status": "error",
                "message": "ストリームは見つかりましたが、URLがありませんでした。"
            }
            return jsonify(response), 500

    except Exception as e:
        # 発生した例外を捕捉し、その内容をJSONレスポンスに含める
        error_message = str(e)
        print(f'エラーが発生しました: {error_message}')
        response = {
            "status": "error",
            "message": "動画ストリームURLの取得中にエラーが発生しました。",
            "error_details": error_message  # ここで具体的なエラー内容を返す
        }
        return jsonify(response), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
