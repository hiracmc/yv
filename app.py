import os
import traceback
from flask import Flask, request, jsonify
from pytube import YouTube
from pytube.exceptions import PytubeError, VideoUnavailable, RegexMatchError

# Flaskアプリケーションのインスタンスを作成
app = Flask(__name__)

# --- ヘルパー関数: レスポンス生成 ---

def create_success_response(video_info):
    """成功時のJSONレスポンスを生成する"""
    response_data = {
        "status": "success",
        "data": video_info
    }
    return jsonify(response_data), 200

def create_error_response(message, error_code, status_code):
    """エラー時のJSONレスポンスを生成する"""
    response_data = {
        "status": "error",
        "error": {
            "code": error_code,
            "message": message
        }
    }
    return jsonify(response_data), status_code

# --- メインロジック ---

def get_youtube_video_info(video_id):
    """
    YouTube動画の情報を取得し、整形して返す。
    エラーが発生した場合はPytubeErrorを投げる。
    """
    try:
        app.logger.info(f"'{video_id}'の動画情報取得を開始します。")
        yt = YouTube(f'https://www.youtube.com/watch?v={video_id}')
        
        # age-restricted動画は情報取得に一手間かかることがあるため明示的にチェック
        yt.bypass_age_gate() 
        
        stream = yt.streams.get_highest_resolution()

        if not stream or not stream.url:
            raise PytubeError("ストリームは見つかりましたが、有効なURLがありませんでした。")

        video_info = {
            "stream_url": stream.url
        }
        app.logger.info(f"'{video_id}'の動画情報取得に成功しました。")
        return video_info

    except (VideoUnavailable, RegexMatchError, PytubeError) as e:
        # Pytube関連のエラーはそのまま上に投げて、ルート関数で処理する
        raise e
    except Exception as e:
        # その他の予期せぬエラーはPytubeErrorにラップして投げる
        raise PytubeError(f"予期せぬ内部エラー: {str(e)}")


# --- ルート定義 (APIエンドポイント) ---

@app.route('/')
def main_route():
    video_id = request.args.get('i')

    if not video_id:
        app.logger.warning("リクエストに 'i' パラメータがありませんでした。")
        return create_error_response(
            "URLに 'i' パラメータ（YouTube動画ID）を指定してください。",
            "INVALID_PARAMETER",
            400  # Bad Request
        )

    try:
        video_info = get_youtube_video_info(video_id)
        return create_success_response(video_info)

    except VideoUnavailable as e:
        app.logger.warning(f"動画 '{video_id}' が利用不可でした: {e}")
        return create_error_response(
            f"動画 '{video_id}' は存在しないか、非公開、または地域制限されています。",
            "VIDEO_UNAVAILABLE",
            404  # Not Found
        )
    except RegexMatchError as e:
        app.logger.error(f"Pytubeの解析エラーが発生しました: {e}。ライブラリの更新が必要な可能性があります。")
        return create_error_response(
            "YouTubeの動画情報解析に失敗しました。YouTube側の仕様変更が原因の可能性があります。",
            "YOUTUBE_PARSE_ERROR",
            503  # Service Unavailable
        )
    except PytubeError as e:
        app.logger.error(f"Pytubeの処理中にエラーが発生しました: {e}")
        return create_error_response(
            f"動画処理中にエラーが発生しました: {e}",
            "PYTUBE_ERROR",
            500  # Internal Server Error
        )
    except Exception:
        # 完全に予期しないエラーはスタックトレース全体をログに残す
        tb_str = traceback.format_exc()
        app.logger.critical(f"予期せぬ致命的なエラーが発生しました:\n{tb_str}")
        return create_error_response(
            "サーバー内部で予期せぬエラーが発生しました。管理者に連絡してください。",
            "INTERNAL_SERVER_ERROR",
            500  # Internal Server Error
        )

# ローカルでのテスト実行用
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
