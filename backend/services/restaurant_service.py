"""
レストラン推薦サービス
OpenAIサービスとPlacesサービスを組み合わせて、総合的なレストラン推薦を提供
"""
from typing import Dict, Any, List
from .openai_service import OpenAIService
from .places_service import PlacesService


class RestaurantService:
    """レストラン推薦の統合サービス"""
    
    def __init__(self):
        """サービスの初期化"""
        self.openai_service = OpenAIService()
        self.places_service = PlacesService()
        self.user_preferences = {}  # 将来のLevel 2実装用
    
    def search_restaurants(self, user_input: str, conversation_history: list = None, last_conditions: dict = None, page: int = 1) -> Dict[str, Any]:
        """
        ユーザーの自然言語入力から適切なレストランを検索・推薦
        
        Args:
            user_input: ユーザーの自然言語入力
            conversation_history: 会話履歴のリスト
            last_conditions: 前回の検索条件
            page: ページ番号
            
        Returns:
            Dict[str, Any]: 検索結果と推薦レストラン
        """
        try:
            # 1. 自然言語から条件を抽出（会話履歴を考慮）
            # ページ2以降でクエリが空の場合は前回の条件を使用
            if page > 1 and not user_input.strip() and last_conditions:
                conditions = last_conditions
            else:
                conditions = self.openai_service.extract_conditions_from_text(
                    user_input, 
                    conversation_history=conversation_history, 
                    last_conditions=last_conditions
                )
            
            if not conditions:
                return {
                    'message': '検索条件を理解できませんでした。もう一度お試しください。',
                    'conditions': {},
                    'restaurants': [],
                    'has_more': False
                }
            
            # 2. 条件に基づいてレストランを検索
            search_result = self.places_service.search_restaurants(conditions, page)
            restaurants = search_result.get('restaurants', [])
            has_more = search_result.get('has_more', False)
            
            if not restaurants:
                cuisine_type = conditions.get('cuisine_type', '指定された条件')
                location = conditions.get('location', '')
                location_msg = f"{location}の" if location else ""
                
                return {
                    'message': f"{location_msg}{cuisine_type}のお店は見つかりませんでした。条件を変更してお試しください。",
                    'conditions': conditions,
                    'restaurants': [],
                    'has_more': False
                }
            
            # 3. AIによるスコアリングと推薦
            recommendations = self.openai_service.score_restaurants(restaurants, conditions)
            
            # デバッグ: レストランデータの確認
            for i, restaurant in enumerate(restaurants[:2]):  # 最初の2つだけログ出力
                print(f"元のレストランデータ {i+1}: {restaurant.get('name', '')} - price_level_text: {restaurant.get('price_level_text', 'なし')}")
            
            for i, recommendation in enumerate(recommendations[:2]):  # 最初の2つだけログ出力
                print(f"推薦データ {i+1}: {recommendation.get('name', '')} - price_level_text: {recommendation.get('price_level_text', 'なし')}")
            
            # 4. 結果のフォーマット
            message = self._format_success_message(recommendations, conditions)
            
            return {
                'message': message,
                'conditions': conditions,
                'restaurants': recommendations,
                'has_more': has_more
            }
            
        except Exception as e:
            print(f"レストラン検索エラー: {e}")
            return {
                'message': 'サーバーエラーが発生しました。しばらくしてからもう一度お試しください。',
                'conditions': {},
                'restaurants': []
            }
    
    def _format_success_message(self, recommendations: List[Dict], conditions: Dict[str, Any]) -> str:
        """
        成功時のメッセージをフォーマット
        
        Args:
            recommendations: 推薦レストランのリスト
            conditions: 検索条件
            
        Returns:
            str: フォーマットされたメッセージ
        """
        if not recommendations:
            return "条件に合うお店が見つかりませんでした。"
        
        count = len(recommendations)
        
        # 条件に応じたメッセージのカスタマイズ
        location = conditions.get('location', '')
        cuisine_type = conditions.get('cuisine_type', '')
        
        if location and cuisine_type:
            base_msg = f"{location}の{cuisine_type}"
        elif location:
            base_msg = f"{location}のお店"
        elif cuisine_type:
            base_msg = f"{cuisine_type}のお店"
        else:
            base_msg = "お店"
        
        if count == 1:
            return f"{base_msg}を1件見つかりました！"
        else:
            return f"{base_msg}の候補が{count}件見つかりました！"
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        サービスの健全性をチェック
        
        Returns:
            Dict[str, Any]: ヘルスチェック結果
        """
        status = {
            'status': 'OK',
            'services': {
                'openai': 'OK',
                'places': 'OK' if self.places_service.client else 'WARNING'
            },
            'message': 'Restaurant AI API is running'
        }
        
        if not self.places_service.client:
            status['services']['places'] = 'WARNING'
            status['message'] += ' (Google Places API key not configured - using mock data)'
        
        return status
