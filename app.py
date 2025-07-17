#ライブラリ
import numpy as np
import matplotlib as plt
import pandas as pd
import scikit-learn
import re
from flask import Flask, request
from urllib.parse import urlparse, parse_qs
from pytube import YouTube

# URLからiパラメータを取得する関数
def get_i_parameter(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    return query_params.get('i', [None])[0]

# YouTubeの動画ストリームURLを取得する関数
def get_youtube_stream_url(video_id):
    try:
        # YouTubeオブジェクトを作成
        yt = YouTube(f'https://www.youtube.com/watch?v={video_id}')
        
        # 最高画質の動画ストリームを取得
        stream = yt.streams.get_highest_resolution()
        
        # ストリームURLを返す
        return stream.url
    except Exception as e:
        print(f'エラーが発生しました: {str(e)}')
        return None

# メイン処理
if __name__ == '__main__':
    # テスト用URL（実際の使用時は適切なURLに変更してください）
    test_url = 'https://www.example.com/watch?v=dQw4w9WgXcQ&i=abcdefg'
    
    # iパラメータを取得
    i_param = get_i_parameter(request.url)
    
    if i_param:
        print(f'取得したiパラメータ: {i_param}')
        
        # YouTubeの動画ストリームURLを取得
        stream_url = get_youtube_stream_url(i_param)
        
        if stream_url:
            print(f'YouTubeの動画ストリームURL: {stream_url}')
        else:
            print('動画ストリームURLの取得に失敗しました。')
    else:
        print('iパラメータが見つかりませんでした。')
