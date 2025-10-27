import os
from dotenv import load_dotenv
from pathlib import Path

# プロジェクトルートディレクトリを特定
project_root = Path(__file__).parent
load_dotenv(project_root / '.env.local')
load_dotenv(project_root / '.env')

class Config:
    # 環境変数から取得
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    GOOGLE_PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')
    
    # Flask設定
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # デフォルトの会社位置（渋谷を例として設定）
    COMPANY_LOCATION = {
        'lat': 35.6598,
        'lng': 139.7006,
        'name': '渋谷'
    }
    
    @classmethod
    def validate_config(cls):
        """設定の検証"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY が設定されていません。.envファイルに設定してください。")
        if not cls.GOOGLE_PLACES_API_KEY:
            print("警告: GOOGLE_PLACES_API_KEY が設定されていません。.envファイルに設定してください。モックデータを使用します。")