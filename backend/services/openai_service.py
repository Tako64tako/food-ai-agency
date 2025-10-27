"""
OpenAI APIを使用した自然言語処理サービス
"""
import json
import re
from typing import Dict, Any, List
from openai import OpenAI
import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config


class OpenAIService:
    """OpenAI APIを使用した自然言語処理サービス"""
    
    def __init__(self):
        """OpenAIクライアントの初期化"""
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
    
    def extract_conditions_from_text(self, user_input: str, conversation_history: list = None, last_conditions: dict = None) -> Dict[str, Any]:
        """
        ユーザーの自然言語入力から検索条件を抽出（会話履歴を考慮）
        
        Args:
            user_input: ユーザーの入力テキスト
            conversation_history: 会話履歴のリスト
            last_conditions: 前回の検索条件
            
        Returns:
            Dict[str, Any]: 抽出された条件
        """
        try:
            # 会話履歴を考慮したプロンプトの構築
            context_info = ""
            if conversation_history and len(conversation_history) > 1:
                context_info += f"\n\n会話履歴:\n"
                for i, msg in enumerate(conversation_history[:-1]):  # 最新のメッセージ以外
                    context_info += f"{i+1}. {msg}\n"
            
            if last_conditions:
                context_info += f"\n前回の検索条件: {json.dumps(last_conditions, ensure_ascii=False)}\n"
            
            user_content = user_input
            if context_info:
                user_content = f"最新の入力: {user_input}{context_info}\n\n上記の会話履歴と前回の検索条件を考慮して、最新の入力から検索条件を抽出してください。前回の条件を引き継ぎつつ、新しい条件で更新または追加してください。"

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": self._get_condition_extraction_prompt()
                    },
                    {
                        "role": "user",
                        "content": user_content
                    }
                ],
                temperature=0.3,
                max_tokens=1200
            )
            
            content = response.choices[0].message.content
            return self._parse_json_response(content)
            
        except Exception as e:
            print(f"OpenAI条件抽出エラー: {e}")
            return {}
    
    def score_restaurants(self, restaurants: List[Dict], conditions: Dict[str, Any]) -> List[Dict]:
        """
        レストランリストを条件に基づいてスコアリング
        
        Args:
            restaurants: レストランのリスト
            conditions: 検索条件
            
        Returns:
            List[Dict]: スコアリングされたレストランのリスト
        """
        try:
            # 元のレストランデータを保持するためのマップを作成
            restaurant_map = {restaurant.get('name', ''): restaurant for restaurant in restaurants}
            
            restaurants_info = json.dumps(restaurants, ensure_ascii=False, indent=2)
            conditions_info = json.dumps(conditions, ensure_ascii=False, indent=2)
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": self._get_scoring_prompt()
                    },
                    {
                        "role": "user",
                        "content": f"検索条件:\n{conditions_info}\n\nレストラン一覧:\n{restaurants_info}"
                    }
                ],
                temperature=0.3,
                max_tokens=1200  # トークン制限を調整
            )
            
            content = response.choices[0].message.content
            result = self._parse_json_response(content)
            scored_restaurants = result.get('recommendations', [])
            
            # AIのスコアリング結果と元のレストランデータをマージ
            final_restaurants = []
            for scored_restaurant in scored_restaurants:
                restaurant_name = scored_restaurant.get('name', '')
                original_restaurant = restaurant_map.get(restaurant_name, {})
                
                # 元のデータを基にして、AIのスコアと推薦理由を追加
                merged_restaurant = original_restaurant.copy()
                merged_restaurant['score'] = scored_restaurant.get('score', 0)
                merged_restaurant['reason'] = scored_restaurant.get('reason', '')
                
                final_restaurants.append(merged_restaurant)
            
            return final_restaurants
            
        except Exception as e:
            print(f"OpenAIスコアリングエラー: {e}")
            return []
    
    def _get_condition_extraction_prompt(self) -> str:
        """条件抽出用のプロンプトを取得"""
        return """
あなたは日本の飲食店検索の専門家です。ユーザーの自然言語入力から以下の条件を抽出してJSONで返してください。

**重要**: 会話履歴と前回の検索条件が提供された場合、それらを考慮して検索条件を統合してください。新しい入力は前回の条件を「更新」または「追加」するものとして扱ってください。

抽出する項目：
- cuisine_type: 料理のジャンル（中華、和食、イタリアン、フレンチ、居酒屋、カフェ等）
- location: 場所（渋谷、新宿、銀座等の地名）
- time: 時間（ランチ、ディナー、または具体的な時間）
- party_size: 人数（数値）
- budget: 予算感（安い、普通、高級、または具体的な金額）
- atmosphere: 雰囲気（静か、賑やか、カジュアル、フォーマル、おしゃれ等）
- special_requirements: 特別な要求（個室、禁煙、お酒、デート向け等）

**会話の継続性**：
- 前回の検索条件が提供されている場合、それをベースにして新しい条件を追加・更新してください
- 明示的に変更された条件のみ更新し、言及されていない条件は前回のものを保持してください
- 例：前回「新宿のフレンチ」で検索し、今回「予算5000円」が追加された場合、locationとcuisine_typeは保持し、budgetを追加してください

注意事項：
- JSONフォーマットで回答してください
- 推測での補完は最小限にしてください
- 会話履歴がない場合は、通常通り現在の入力のみから条件を抽出してください

基本例：
入力: "渋谷で夜7時から静かなお店で3人でお酒を飲みたい"
出力: {
    "cuisine_type": "居酒屋",
    "location": "渋谷",
    "time": "19:00",
    "party_size": 3,
    "atmosphere": "静か",
    "special_requirements": "お酒"
}

継続例：
前回の条件: {"cuisine_type": "フレンチ", "location": "新宿", "special_requirements": "デート向け"}
最新入力: "予算は5000円ほどでお願いします"
出力: {
    "cuisine_type": "フレンチ",
    "location": "新宿",
    "budget": "5000円",
    "special_requirements": "デート向け"
}
"""
    
    def _get_scoring_prompt(self) -> str:
        """スコアリング用のプロンプトを取得"""
        return """
あなたは飲食店推薦の専門家です。与えられた検索条件とレストランリストから、
各レストランを0-100のスコアで評価し、上位3つを選んで推薦理由と共に返してください。

評価基準：
1. 条件との一致度（50点）- 料理ジャンル、場所、雰囲気等の合致度
2. 評価・口コミ（30点）- Googleレビューの評価
3. 価格帯の適切さ（20点）- 予算に対する価格帯の適切さ

回答形式（必ずこの形式で回答してください）：
{
    "recommendations": [
        {
            "name": "店名",
            "score": 85,
            "reason": "推薦理由（なぜこの店を選んだのか、条件との合致点を説明）",
            "address": "住所",
            "rating": 4.2
        }
    ]
}

注意事項：
- 必ず上位3つまでを選択してください
- スコアは客観的な基準に基づいて算出してください
- 推薦理由は具体的で分かりやすく説明してください
- JSONフォーマットを厳密に守ってください
"""
    
    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """
        APIレスポンスからJSONを抽出・パース
        
        Args:
            content: APIレスポンスのコンテンツ
            
        Returns:
            Dict[str, Any]: パースされたJSON
        """
        try:
            # 直接JSONパースを試行
            return json.loads(content)
        except json.JSONDecodeError:
            try:
                # JSON部分を正規表現で抽出
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    print(f"JSON形式が見つかりません: {content}")
                    return {}
            except json.JSONDecodeError as e:
                print(f"JSON解析エラー: {e}, コンテンツ: {content}")
                return {}
