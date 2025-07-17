import os
import traceback
from flask import Flask, request, jsonify
import yt_dlp # pytubeの代わりにyt-dlpをインポート

# Flaskアプリケーションのインスタンスを作成
app = Flask(__name__)

# --- ヘルパー関数: レスポンス生成 ---
def create_success_response(video_info):
    """成功時のJSONレスポンスを生成する"""
    response_data = {"status": "success", "data": video_info}
    return jsonify(response_data), 200

def create_error_response(message, error_code, status_code):
    """エラー時のJSONレスポンスを生成する"""
    response_data = {"status": "error", "error": {"code": error_code, "message": message}}
    return jsonify(response_data), status_code

# --- メインロジックをyt-dlp用に書き換え ---
def get_youtube_video_info(video_id):
    """
    yt-dlpを使い、YouTube動画の情報を取得して整形して返す。
    """
    ydl_opts = {
        'format': 'best[ext=mp4]/best', # 最高画質のMP4を優先
        'quiet': True,                  # コンソールへの出力を抑制
        'no_warnings': True,            # 警告を抑制
        'nocheckcertificate': True,     # SSL証明書の検証をスキップ
        'source_address': '0.0.0.0'     # IPv4でリクエストを試みる
    }
    video_url = f'https://www.youtube.com/watch?v={video_id}'

    try:
        app.logger.info(f"'{video_id}'の動画情報取得を開始します (using yt-dlp)。")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 動画情報を辞書として抽出（ダウンロードはしない）
            info_dict = ydl.extract_info(video_url, download=False)
            
            # 必要な情報を抽出して整形
            video_info = {
                "video_id": info_dict.get('id'),
                "title": info_dict.get('title'),
                "author": info_dict.get('uploader'),
                "length_seconds": info_dict.get('duration'),
                "stream_url": info_dict.get('url') # yt-dlpは直接ストリームURLをくれる
            }
        
        app.logger.info(f"'{video_id}'の動画情報取得に成功しました (using yt-dlp)。")
        return video_info
        
    except yt_dlp.utils.DownloadError as e:
        # 動画が存在しない、非公開、地域制限などの場合にこのエラーが発生する
        app.logger.error(f"yt-dlp DownloadError: {e}")
        raise RuntimeError(f"動画の取得に失敗しました。非公開、削除済み、または地域制限されている可能性があります。")
    except Exception as e:
        # その他の予期せぬエラー
        app.logger.error(f"予期せぬエラー: {e}")
        raise RuntimeError(f"サーバー内部で予期せぬエラーが発生しました: {e}")

# --- ルート定義 (APIエンドポイント) ---
@app.route('/')
def main_route():
    video_id = request.args.get('i')
    if not video_id:
        return create_error_response("URLに 'i' パラメータ（YouTube動画ID）を指定してください。", "INVALID_PARAMETER", 400)

    try:
        video_info = get_youtube_video_info(video_id)
        if not video_info or not video_info.get("stream_url"):
            raise RuntimeError("ストリームURLの取得に失敗しました。")
            
        return create_success_response(video_info)

    except RuntimeError as e:
        app.logger.error(f"処理エラーが発生しました ('{video_id}'): {e}")
        return create_error_response(str(e), "PROCESSING_ERROR", 500)
    except Exception:
        tb_str = traceback.format_exc()
        app.logger.critical(f"予期せぬ致命的なエラーが発生しました ('{video_id}'):\n{tb_str}")
        return create_error_response("サーバー内部で予期せぬエラーが発生しました。", "INTERNAL_SERVER_ERROR", 500)

@app.route('/healthz')
def health_check():
    return "OK", 200

# --- ローカル実行部分 ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
