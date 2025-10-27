"""
食事処提案AI - メインアプリケーション
Flask APIサーバー
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from services.restaurant_service import RestaurantService
from services.reservation_agent import ReservationAgent

# Flask アプリケーションの初期化
app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])  # Next.jsからのリクエストを許可

# 設定の検証
try:
    Config.validate_config()
except ValueError as e:
    print(f"設定エラー: {e}")

# サービスの初期化
restaurant_service = RestaurantService()
reservation_agent = ReservationAgent()

@app.route('/api/search', methods=['POST'])
def search_restaurants():
    """
    レストラン検索API
    
    POST /api/search
    {
        "query": "渋谷で夜7時から静かなお店で3人でお酒を飲みたい"
    }
    """
    try:
        # リクエストデータの検証
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
        
        user_input = data.get('query', '').strip()
        page = data.get('page', 1)
        last_conditions = data.get('last_conditions', None)
        
        # ページ2以降でクエリが空の場合は、前回の条件での追加検索として処理
        if not user_input and page > 1 and last_conditions:
            print(f"追加読み込み - ページ{page}, 前回の条件: {last_conditions}")
        elif not user_input:
            print(f"クエリが空 - ページ{page}, 前回の条件: {last_conditions}")
            return jsonify({'error': '検索条件を入力してください'}), 400
        
        # 会話履歴を取得
        conversation_history = data.get('conversation_history', [])
        
        # レストラン検索の実行
        result = restaurant_service.search_restaurants(
            user_input, 
            conversation_history=conversation_history, 
            last_conditions=last_conditions,
            page=page
        )
        
        return jsonify(result)
        
    except Exception as e:
        print(f"検索API エラー: {e}")
        return jsonify({
            'error': 'サーバーエラーが発生しました',
            'message': 'しばらくしてからもう一度お試しください'
        }), 500

@app.route('/api/reservation/start', methods=['POST'])
def start_reservation():
    """
    予約プロセス開始API
    
    POST /api/reservation/start
    {
        "restaurant": {...},
        "user_id": "optional_user_id"
    }
    """
    try:
        print("🤖 予約開始APIが呼ばれました")
        data = request.get_json()
        print(f"📥 受信データ: {data}")
        
        if not data or 'restaurant' not in data:
            print("❌ レストラン情報がありません")
            return jsonify({'error': 'レストラン情報が必要です'}), 400
        
        restaurant = data['restaurant']
        user_id = data.get('user_id', 'default')
        print(f"🏪 レストラン: {restaurant.get('name', 'Unknown')}")
        print(f"👤 ユーザーID: {user_id}")
        
        result = reservation_agent.start_reservation(restaurant)
        print(f"📤 予約開始結果: {result}")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ 予約開始API エラー: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'サーバーエラーが発生しました',
            'message': str(e)
        }), 500

@app.route('/api/reservation/step', methods=['POST'])
def process_reservation_step():
    """
    予約ステップ処理API
    
    POST /api/reservation/step
    {
        "session_id": "session_id",
        "user_input": "ユーザーの入力"
    }
    """
    try:
        print("📤 予約ステップAPIが呼ばれました")
        data = request.get_json()
        print(f"📥 受信データ: {data}")
        
        if not data:
            print("❌ JSONデータがありません")
            return jsonify({'error': 'Invalid JSON data'}), 400
        
        session_id = data.get('session_id')
        user_input = data.get('user_input', '').strip()
        print(f"🔑 セッションID: {session_id}")
        print(f"💬 ユーザー入力: {user_input}")
        
        if not session_id:
            print("❌ セッションIDがありません")
            return jsonify({'error': 'セッションIDが必要です'}), 400
        
        if not user_input:
            print("❌ ユーザー入力がありません")
            return jsonify({'error': 'ユーザー入力が必要です'}), 400
        
        result = reservation_agent.process_reservation_step(session_id, user_input)
        print(f"📤 予約ステップ結果: {result}")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ 予約ステップ処理API エラー: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'サーバーエラーが発生しました',
            'message': str(e)
        }), 500

@app.route('/api/reservation/status/<session_id>', methods=['GET'])
def get_reservation_status(session_id):
    """
    予約セッション状態取得API
    
    GET /api/reservation/status/<session_id>
    """
    try:
        result = reservation_agent.get_session_status(session_id)
        return jsonify(result)
        
    except Exception as e:
        print(f"予約状態取得API エラー: {e}")
        return jsonify({
            'error': 'サーバーエラーが発生しました',
            'message': str(e)
        }), 500

@app.route('/api/reservation/cancel/<session_id>', methods=['POST'])
def cancel_reservation(session_id):
    """
    予約セッションキャンセルAPI
    
    POST /api/reservation/cancel/<session_id>
    """
    try:
        result = reservation_agent.cancel_session(session_id)
        return jsonify(result)
        
    except Exception as e:
        print(f"予約キャンセルAPI エラー: {e}")
        return jsonify({
            'error': 'サーバーエラーが発生しました',
            'message': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    ヘルスチェックAPI
    
    GET /api/health
    """
    try:
        health_status = restaurant_service.get_health_status()
        return jsonify(health_status)
    except Exception as e:
        print(f"ヘルスチェック エラー: {e}")
        return jsonify({
            'status': 'ERROR',
            'message': f'Health check failed: {str(e)}'
        }), 500

@app.errorhandler(404)
def not_found(error):
    """404エラーハンドラ"""
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested endpoint does not exist'
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """405エラーハンドラ"""
    return jsonify({
        'error': 'Method Not Allowed',
        'message': 'The method is not allowed for the requested URL'
    }), 405

@app.errorhandler(500)
def internal_server_error(error):
    """500エラーハンドラ"""
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An internal server error occurred'
    }), 500

if __name__ == '__main__':
    app.run(
        debug=Config.FLASK_DEBUG,
        host='0.0.0.0',
        port=8000
    )
