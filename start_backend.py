#!/usr/bin/env python3
"""
食事処提案AI バックエンドサーバー起動スクリプト
"""
import os
import sys
from pathlib import Path

# プロジェクトルートディレクトリの設定
PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "backend"

def check_requirements():
    """必要な環境とファイルをチェック"""
    print("🔍 環境チェック中...")
    
    # Pythonバージョン確認
    python_version = sys.version_info
    print(f"Python バージョン: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8):
        print("❌ Python 3.8以上が必要です")
        return False
    
    # 必要なファイルの存在確認
    required_files = [
        PROJECT_ROOT / "config.py",
        BACKEND_DIR / "app.py",
        BACKEND_DIR / "services" / "restaurant_service.py",
        BACKEND_DIR / "services" / "openai_service.py",
        BACKEND_DIR / "services" / "places_service.py",
        PROJECT_ROOT / "requirements.txt"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not file_path.exists():
            missing_files.append(str(file_path))
    
    if missing_files:
        print("❌ 以下のファイルが見つかりません:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ 必要なファイルが確認できました")
    return True

def check_dependencies():
    """依存関係の確認"""
    print("\n📦 依存関係チェック中...")
    
    required_packages = ['flask', 'flask_cors', 'openai', 'googlemaps', 'dotenv']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ 以下のパッケージがインストールされていません:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n以下のコマンドで依存関係をインストールしてください:")
        print("pip install -r requirements.txt")
        return False
    
    print("✅ 必要なパッケージがインストールされています")
    return True

def show_config_info():
    """設定情報の表示"""
    print("\n⚙️  設定情報:")
    
    # パスをPYTHONPATHに追加
    sys.path.insert(0, str(PROJECT_ROOT))
    
    try:
        from config import Config
        
        # OpenAI APIキー
        if Config.OPENAI_API_KEY and not Config.OPENAI_API_KEY.startswith('your_'):
            print("✅ OpenAI APIキー: 設定済み")
        else:
            print("⚠️  OpenAI APIキー: 未設定または無効")
        
        # Google Places APIキー
        if Config.GOOGLE_PLACES_API_KEY and not Config.GOOGLE_PLACES_API_KEY.startswith('your_'):
            print("✅ Google Places APIキー: 設定済み")
        else:
            print("⚠️  Google Places APIキー: 未設定（モックデータを使用）")
            
        print(f"🏢 会社所在地: {Config.COMPANY_LOCATION['name']}")
        
    except Exception as e:
        print(f"❌ 設定読み込みエラー: {e}")

def start_server():
    """サーバーの起動"""
    print("\n🚀 サーバーを起動中...")
    print("📍 URL: http://localhost:5000")
    print("📋 ヘルスチェック: http://localhost:5000/api/health")
    print("🔄 停止するには Ctrl+C を押してください")
    print("-" * 50)
    
    # パスをPYTHONPATHに追加
    sys.path.insert(0, str(PROJECT_ROOT))
    sys.path.insert(0, str(BACKEND_DIR))
    
    # バックエンドディレクトリに移動
    os.chdir(BACKEND_DIR)
    
    # アプリケーションを実行
    from app import app
    app.run(debug=False, host='0.0.0.0', port=5000)

def main():
    """メイン関数"""
    print("🍽️  食事処提案AI バックエンドサーバー")
    print("=" * 50)
    
    # 環境チェック
    if not check_requirements():
        sys.exit(1)
    
    if not check_dependencies():
        sys.exit(1)
    
    # 設定情報表示
    show_config_info()
    
    # サーバー起動
    try:
        start_server()
    except KeyboardInterrupt:
        print("\n\n👋 サーバーを停止しました")
    except Exception as e:
        print(f"\n❌ サーバー起動エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
