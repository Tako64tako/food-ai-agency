"""
Google Places APIを使用した場所検索サービス
"""
from typing import Dict, Any, Optional
import googlemaps
import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config


class PlacesService:
    """Google Places APIを使用した場所検索サービス"""
    
    def __init__(self):
        """Google Maps クライアントの初期化"""
        try:
            self.client = googlemaps.Client(key=Config.GOOGLE_PLACES_API_KEY)
        except Exception as e:
            print(f"Google Maps クライアント初期化エラー: {e}")
            self.client = None
    
    def search_restaurants(self, conditions: Dict[str, Any], page: int = 1) -> Dict[str, Any]:
        """
        条件に基づいてレストランを検索
        
        Args:
            conditions: 検索条件
            page: ページ番号（1から開始）
            
        Returns:
            Dict[str, Any]: 検索されたレストランのリストとページネーション情報
        """
        if not self.client:
            print("Google Maps クライアントが初期化されていません")
            return self._get_mock_restaurants(conditions, page)
        
        try:
            # 検索クエリの構築
            query = self._build_search_query(conditions)
            location = conditions.get('location', Config.COMPANY_LOCATION['name'])
            
            # ページサイズの設定
            page_size = 5  # 1ページあたり5件
            
            # Google Places Text Search
            places_result = self.client.places(
                query=f"{query} {location}",
                language='ja',
                type='restaurant',
                region='jp'
            )
            
            all_results = places_result.get('results', [])
            
            # ページネーション処理
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            current_page_results = all_results[start_idx:end_idx]
            
            restaurants = []
            for place in current_page_results:
                restaurant = self._format_restaurant_data(place)
                if restaurant:
                    restaurants.append(restaurant)
            
            # 次のページがあるかを判定
            has_more = end_idx < len(all_results)
            
            return {
                'restaurants': restaurants,
                'has_more': has_more,
                'page': page,
                'total_results': len(all_results)
            }
            
        except Exception as e:
            print(f"Google Places検索エラー: {e}")
            return self._get_mock_restaurants(conditions, page)
    
    def _build_search_query(self, conditions: Dict[str, Any]) -> str:
        """
        検索条件からクエリ文字列を構築
        
        Args:
            conditions: 検索条件
            
        Returns:
            str: 検索クエリ
        """
        query_parts = []
        
        # 料理タイプ
        cuisine_type = conditions.get('cuisine_type')
        if cuisine_type:
            query_parts.append(cuisine_type)
        
        # 特別な要求
        special_requirements = conditions.get('special_requirements')
        if special_requirements and 'お酒' in special_requirements:
            if not cuisine_type or cuisine_type not in ['居酒屋', 'バー']:
                query_parts.append('居酒屋')
        
        # 基本的なレストラン検索
        if not query_parts:
            query_parts.append('レストラン')
        else:
            query_parts.append('レストラン')
        
        return ' '.join(query_parts)
    
    def _format_restaurant_data(self, place: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Google Places APIのレスポンスを内部形式に変換
        
        Args:
            place: Google Places APIのplace情報
            
        Returns:
            Optional[Dict[str, Any]]: フォーマットされたレストラン情報
        """
        try:
            # 写真URLの生成
            photo_url = None
            if place.get('photos') and len(place['photos']) > 0:
                photo_reference = place['photos'][0].get('photo_reference')
                if photo_reference:
                    # Google Places Photo APIのURL構築
                    photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_reference}&key={Config.GOOGLE_PLACES_API_KEY}"
            
            # 価格帯の文字列変換
            price_level_text = self._format_price_level(place.get('price_level', 0))
            
            # 詳細情報を取得（Place Details API）
            place_details = self._get_place_details(place.get('place_id', ''))
            
            return {
                'name': place.get('name', ''),
                'address': place.get('formatted_address', ''),
                'rating': place.get('rating', 0),
                'price_level': place.get('price_level', 0),
                'price_level_text': price_level_text,
                'place_id': place.get('place_id', ''),
                'types': place.get('types', []),
                'user_ratings_total': place.get('user_ratings_total', 0),
                'vicinity': place.get('vicinity', ''),
                'geometry': place.get('geometry', {}),
                'photo_url': photo_url,
                'website': place_details.get('website', ''),
                'phone_number': place_details.get('formatted_phone_number', ''),
                'opening_hours': place_details.get('opening_hours', {}),
                'url': place_details.get('url', '')  # Google MapsページのURL
            }
        except Exception as e:
            print(f"レストランデータフォーマットエラー: {e}")
            return None
    
    def _format_price_level(self, price_level: int) -> str:
        """
        価格レベルを日本語の説明に変換
        
        Args:
            price_level: Google Places APIの価格レベル（0-4）
            
        Returns:
            str: 価格帯の説明
        """
        price_levels = {
            0: "価格帯未設定",
            1: "リーズナブル（¥）",
            2: "普通（¥¥）", 
            3: "やや高め（¥¥¥）",
            4: "高級（¥¥¥¥）"
        }
        return price_levels.get(price_level, "価格情報なし")
    
    def _get_place_details(self, place_id: str) -> Dict[str, Any]:
        """
        Place Details APIで詳細情報を取得
        
        Args:
            place_id: Google Places APIのplace_id
            
        Returns:
            Dict[str, Any]: 詳細情報
        """
        if not self.client or not place_id:
            return {}
        
        try:
            # Place Details APIを呼び出し
            details_result = self.client.place(
                place_id=place_id,
                fields=['website', 'formatted_phone_number', 'opening_hours', 'url'],
                language='ja'
            )
            
            return details_result.get('result', {})
            
        except Exception as e:
            print(f"Place Details API エラー: {e}")
            return {}
    
    def _get_mock_restaurants(self, conditions: Dict[str, Any], page: int = 1) -> Dict[str, Any]:
        """
        Google Places APIが利用できない場合のモックデータ
        
        Args:
            conditions: 検索条件
            page: ページ番号
            
        Returns:
            Dict[str, Any]: モックレストランデータとページネーション情報
        """
        cuisine_type = conditions.get('cuisine_type', '和食')
        location = conditions.get('location', '渋谷')
        
        # テスト用により多くのモックデータを生成
        mock_restaurants = []
        for i in range(12):  # 12件のデータを生成（ページネーションをテストするため）
            restaurant = {
                'name': f'{cuisine_type}レストラン {chr(65+i)} ({location})',
                'address': f'東京都{location}区 {i+1}-{i+1}-{i+1}',
                'rating': round(3.5 + (i % 3) * 0.3, 1),
                'price_level': (i % 4) + 1,
                'price_level_text': ['リーズナブル（¥）', '普通（¥¥）', 'やや高め（¥¥¥）', '高級（¥¥¥¥）'][i % 4],
                'place_id': f'mock_place_id_{i+1}',
                'types': ['restaurant', 'food'],
                'user_ratings_total': 50 + (i * 20),
                'vicinity': f'{location}駅周辺',
                'geometry': {'location': {'lat': 35.6598 + (i * 0.001), 'lng': 139.7006 + (i * 0.001)}},
                'website': f'https://example-restaurant-{chr(97+i)}.com' if i % 2 == 0 else '',
                'phone_number': f'03-{1000+i}-{5000+i}',
                'opening_hours': {'open_now': i % 3 != 0},
                'url': f'https://maps.google.com/?cid={12345+i}',
                'photo_url': None
            }
            mock_restaurants.append(restaurant)
        
        # ページネーション処理
        page_size = 5
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        current_page_results = mock_restaurants[start_idx:end_idx]
        
        has_more = end_idx < len(mock_restaurants)
        
        print(f"モックデータ - ページ{page}: {start_idx}-{end_idx} / 全{len(mock_restaurants)}件, 次のページあり: {has_more}")
        
        return {
            'restaurants': current_page_results,
            'has_more': has_more,
            'page': page,
            'total_results': len(mock_restaurants)
        }
