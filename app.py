import os
from flask import Flask, request
from urllib.parse import urlparse, parse_qs
from pytube import YouTube

# Flaskアプリケーションのインスタンスを作成
app = Flask(__name__)

# URLからiパラメータを取得する関数（この関数は今回直接使いませんが、構造理解のために残します）
def get_i_parameter(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    return query_params.get('i', [None])[0]

# YouTubeの動画ストリームURLを取得する関数
def get_youtube_stream_url(video_id):
    try:
        yt = YouTube(f'https://www.youtube.com/watch?v={video_id}')
        # 最高画質の動画ストリームを取得
        stream = yt.streams.get_highest_resolution()
        # ストリームURLを返す
        return stream.url
    except Exception as e:
        print(f'エラーが発生しました: {str(e)}')
        return None

# '/' ルートへのリクエストを処理する関数
@app.route('/')
def main():
    # URLのクエリパラメータから 'i' を取得
    # 例: https://your-service-name.onrender.com/?i=dQw4w9WgXcQ
    video_id = request.args.get('i')

    if video_id:
        print(f'取得したiパラメータ (video_id): {video_id}')

        # YouTubeの動画ストリームURLを取得
        stream_url = get_youtube_stream_url(video_id)

        if stream_url:
            # 成功した場合、ストリームURLを返す（リダイレクトやJSON形式など、用途に応じて変更）
            return f'YouTube Stream URL: <a href="{stream_url}">{stream_url}</a>'
        else:
            return '動画ストリームURLの取得に失敗しました。', 500
    else:
        return 'URLに "i" パラメータが見つかりませんでした。例: /?i=your_video_id', 400

# ローカルでのテスト実行用（RenderではGunicornがこれに代わります）
if __name__ == '__main__':
    # RenderはPORT環境変数を指定するため、それを取得。なければ5000をデフォルトに。
    port = int(os.environ.get('PORT', 5000))
    # '0.0.0.0'でリッスンすることで、外部からのアクセスを許可
    app.run(host='0.0.0.0', port=port)
