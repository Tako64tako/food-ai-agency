"""
予約代行エージェントサービス
Puppeteer MCP Serverを使用してレストラン予約を自動化
"""
from typing import Dict, Any, Optional
from datetime import datetime
from openai import OpenAI
from config import Config
from .puppeteer_mcp_client import PuppeteerMCPClient
from .tabelog_reservation import tabelog_service
from .toreta_reservation import toreta_service


class ReservationAgent:
    """予約代行エージェント"""
    
    def __init__(self):
        """エージェントの初期化"""
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.reservation_sessions = {}  # セッション管理
        self.puppeteer_client = PuppeteerMCPClient()

    def _check_restaurant_booking_availability(self, restaurant: Dict[str, Any]) -> Dict[str, Any]:
        """
        レストランの予約可能性を事前チェック
        
        Args:
            restaurant: レストラン情報
            
        Returns:
            Dict[str, Any]: 予約可能性情報
        """
        print(f"🔍 予約可能性チェック開始: {restaurant.get('name', 'Unknown')}")
        
        name = restaurant.get('name', '').lower()
        website = restaurant.get('website', '')
        phone_number = restaurant.get('phone_number', '')
        
        # 実際のレストラン予約システムの分析
        # デモでは、いくつかの条件に基づいて予約可能性を判定
        
        # 大手チェーン店は通常オンライン予約システムを持っている
        chain_restaurants = [
            'すかいらーく', 'ガスト', 'ジョナサン', 'バーミヤン', 'ココス',
            'くら寿司', 'スシロー', 'はま寿司', 'かっぱ寿司',
            'マクドナルド', 'ケンタッキー', 'モスバーガー',
            'デニーズ', 'ロイヤルホスト', 'ビッグボーイ',
            '鳥貴族', '和民', '魚民', '白木屋', '笑笑'
        ]
        
        # 高級レストランは通常電話予約のみ
        upscale_keywords = ['割烹', '懐石', 'フレンチ', 'イタリアン', '鉄板焼', '寿司', '天ぷら', '和食', '日本料理', '料亭', '会席']
        
        # 小規模個人経営店は電話予約が多い
        small_business_keywords = ['家族経営', '個人店', '隠れ家', 'カウンター', '大将', 'マスター', '本格', '老舗', '創業']
        
        # 中華料理店も電話予約が多い傾向
        chinese_keywords = ['中華', '中国', '四川', '広東', '北京', '上海', '点心', '飲茶', '星', '龍', '鳳', '麺', '餃子']
        
        is_chain = any(chain in name for chain in chain_restaurants)
        is_upscale = any(keyword in name for keyword in upscale_keywords)
        is_small_business = any(keyword in name for keyword in small_business_keywords)
        is_chinese = any(keyword in name for keyword in chinese_keywords)
        
        print(f"📊 分析結果: チェーン店={is_chain}, 高級店={is_upscale}, 個人店={is_small_business}, 中華={is_chinese}")
        print(f"📞 電話番号: {phone_number}")
        print(f"🌐 ウェブサイト: {website}")
        
        # 予約可能性の判定ロジック（より多くのレストランで予約を試行）
        if is_chain and (website or phone_number):
            return {
                'available': True,
                'method': 'web_form',
                'method_description': 'オンライン予約システム（チェーン店）',
                'confidence': 0.8
            }
        elif website and any(keyword in website.lower() for keyword in ['reservation', '予約', 'booking', 'table']):
            return {
                'available': True,
                'method': 'web_form',
                'method_description': 'ウェブサイト予約フォーム',
                'confidence': 0.9
            }
        elif phone_number:
            # 特定の高級レストランのみ電話予約案内
            exclusive_phone_only = ['割烹', '懐石', '料亭', '会席']
            if any(keyword in name for keyword in exclusive_phone_only):
                return {
                    'available': False,
                    'reason': 'このレストランは電話予約のみ対応しています（高級店のため）',
                    'method': 'phone_only',
                    'phone_number': phone_number,
                    'alternative_methods': [
                        f'📞 直接お電話: {phone_number}',
                        '🌐 予約サイト（ぐるなび、食べログ、ホットペッパーなど）',
                        '🚶 店舗への直接来店'
                    ]
                }
            else:
                # その他のレストランはWeb予約を試行（失敗時は電話案内）
                return {
                    'available': True,
                    'method': 'web_form',
                    'method_description': 'ウェブサイトまたは電話予約',
                    'confidence': 0.7,
                    'fallback_phone': phone_number
                }
        else:
            return {
                'available': False,
                'reason': '予約システムの情報が不足しています',
                'alternative_methods': [
                    '🌐 レストランの公式サイトを確認',
                    '🚶 店舗への直接来店'
                ]
            }
    
    def start_reservation(self, restaurant: Dict[str, Any]) -> Dict[str, Any]:
        """
        予約セッションを開始
        
        Args:
            restaurant: レストラン情報
            
        Returns:
            Dict[str, Any]: 初期メッセージと状態
        """
        # セッションIDを生成
        session_id = f"{restaurant.get('place_id', 'default')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(self)}"[-50:]
        
        # 予約可能性をチェック
        availability = self._check_restaurant_booking_availability(restaurant)
        
        if not availability['available']:
            message = f"⚠️ **{restaurant.get('name', 'このレストラン')}は現在、オンラインAI予約に対応していません**\n\n"
            message += f"理由: {availability.get('reason', '予約システム未対応')}\n\n"
            
            if availability.get('phone_number'):
                message += f"📞 **直接お電話での予約をお勧めします**: {availability['phone_number']}\n\n"
            
            if availability.get('alternative_methods'):
                message += "🔄 **代替予約方法**:\n"
                for method in availability['alternative_methods']:
                    message += f"• {method}\n"
            
            return {
                'session_id': session_id,
                'message': message,
                'availability_status': 'not_available',
                'alternative_methods': availability.get('alternative_methods', []),
                'end_session': True
            }
        
        # セッションを初期化
        self.reservation_sessions[session_id] = {
            'restaurant': restaurant,
            'data': {
                'datetime': None,
                'party_size': None,
                'contact': None,
                'email': None,
                'special_requests': None
            },
            'step': 'initial',
            'availability': availability
        }
        
        print(f"🎉 新規セッション作成: {session_id}")
        print(f"📊 セッション数: {len(self.reservation_sessions)}")
        
        return {
            'session_id': session_id,
            'message': f"🍽️ **{restaurant.get('name', 'レストラン')}** の予約を開始します！\n\n"
                      f"📍 住所: {restaurant.get('address', '住所不明')}\n"
                      f"📞 電話: {restaurant.get('phone_number', '電話番号なし')}\n\n"
                      f"📅 まず、いつ予約したいですか？\n"
                      f"日時を教えてください。\n"
                      f"例: 「明日の19時」「今週土曜日の12時」「12月25日の18時30分」",
            'step': 'datetime_input',
            'availability_status': 'available',
            'availability_method': availability.get('method', 'unknown'),
            'options': [
                "今日のディナー",
                "明日のランチ",
                "今度の週末",
                "具体的な日時を入力"
            ]
        }
    
    def process_reservation_step(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """
        予約ステップを処理
        
        Args:
            session_id: セッションID
            user_input: ユーザーの入力
            
        Returns:
            Dict[str, Any]: 応答
        """
        print(f"🔍 予約ステップ処理開始: session_id={session_id}, input={user_input}")
        
        if session_id not in self.reservation_sessions:
            print(f"❌ セッションが見つかりません: {session_id}")
            print(f"現在のセッション一覧: {list(self.reservation_sessions.keys())}")
            return {
                'error': 'セッションが見つかりません。新しい予約を開始してください。',
                'restart_needed': True
            }
        
        session = self.reservation_sessions[session_id]
        current_step = session['step']
        print(f"📍 現在のステップ: {current_step}")
        
        try:
            # 'initial' ステップから 'datetime_input' に遷移
            if current_step == 'initial':
                print("🎯 初期ステップから日時入力ステップに遷移")
                session['step'] = 'datetime_input'
                return self._handle_datetime_input(session_id, user_input)
            elif current_step == 'datetime_input':
                return self._handle_datetime_input(session_id, user_input)
            elif current_step == 'party_size_input':
                return self._handle_party_size_input(session_id, user_input)
            elif current_step == 'contact_info_input':
                return self._handle_contact_info_input(session_id, user_input)
            elif current_step == 'email_input':
                return self._handle_email_input(session_id, user_input)
            elif current_step == 'special_requests_input':
                return self._handle_special_requests_input(session_id, user_input)
            elif current_step == 'confirmation':
                return self._handle_confirmation(session_id, user_input)
            else:
                print(f"⚠️ 不明なステップ: {current_step}")
                return {
                    'error': f'不明な処理ステップです: {current_step}',
                    'session_id': session_id,
                    'restart_needed': True
                }
        except Exception as e:
            print(f"❌ ステップ処理エラー: {e}")
            import traceback
            traceback.print_exc()
            return {
                'error': f'処理中にエラーが発生しました: {str(e)}',
                'session_id': session_id
            }
    
    def _handle_datetime_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """日時入力の処理"""
        try:
            print(f"📅 日時入力処理: '{user_input}'")
            
            # 一括フォームデータの場合
            if user_input.startswith('日時:') and '人数:' in user_input and '名前:' in user_input:
                return self._handle_bulk_form_data(session_id, user_input)
            
            # OpenAI APIを使用して自然言語から日時を抽出
            parsed_datetime = self._parse_datetime_with_ai(user_input)
            print(f"🤖 AI解析結果: {parsed_datetime}")
            
            if not parsed_datetime:
                print("❌ 日時解析に失敗")
                return {
                    'message': '申し訳ございません。日時を正しく理解できませんでした。\n'
                              'もう一度、具体的な日時を教えてください。\n'
                              '例: 「12月25日19時」「明日の12時」「来週金曜日の18時30分」',
                    'step': 'datetime_input',
                    'error': True,
                    'options': [
                        "今日のディナー",
                        "明日のランチ", 
                        "今度の週末",
                        "具体的な日時を入力"
                    ]
                }
            
            session = self.reservation_sessions[session_id]
            session['data']['datetime'] = parsed_datetime
            session['step'] = 'party_size_input'
            print("✅ 日時設定完了、次のステップに進行: party_size_input")
            
            formatted_datetime = datetime.fromisoformat(parsed_datetime).strftime('%Y年%m月%d日 %H:%M')
            
            result = {
                'session_id': session_id,  # セッションIDを含める
                'message': f"📅 予約日時: {formatted_datetime}\n\n"
                          f"ありがとうございます！\n"
                          f"次に、お食事される人数を教えてください。",
                'step': 'party_size_input',
                'options': [
                    "1名", "2名", "3名", "4名", "5名", "6名", "その他"
                ],
                'error': False,
                'processing': False
            }
            
            print(f"✅ 日時処理完了: {result}")
            return result
            
        except Exception as e:
            print(f"❌ 日時処理エラー: {e}")
            import traceback
            traceback.print_exc()
            return {
                'message': f'日時の処理でエラーが発生しました: {str(e)}\n'
                          'もう一度お試しください。',
                'step': 'datetime_input',
                'error': True,
                'options': [
                    "今日のディナー",
                    "明日のランチ", 
                    "今度の週末",
                    "具体的な日時を入力"
                ]
            }
    
    def _handle_party_size_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """人数入力の処理"""
        try:
            print(f"👥 人数入力処理: '{user_input}'")
            party_size = self._extract_party_size(user_input)
            
            if not party_size:
                return {
                    'session_id': session_id,
                    'message': '人数を正しく理解できませんでした。\n'
                              '何名様でのご利用でしょうか？\n'
                              '例: 「2名」「3人」',
                    'step': 'party_size_input',
                    'error': True,
                    'options': ["1名", "2名", "3名", "4名", "5名", "6名", "その他"]
                }
            
            session = self.reservation_sessions[session_id]
            session['data']['party_size'] = party_size
            session['step'] = 'contact_info_input'
            print("✅ 人数設定完了、次のステップに進行: contact_info_input")
            
            return {
                'session_id': session_id,
                'message': f"👥 人数: {party_size}名\n\n"
                          f"続いて、予約に必要な連絡先情報を教えてください。\n"
                          f"お名前と電話番号をお願いします。\n"
                          f"例: 「田中太郎 090-1234-5678」",
                'step': 'contact_info_input',
                'options': [
                    "田中太郎 090-1234-5678",
                    "佐藤花子 080-9876-5432", 
                    "山田次郎 070-1111-2222",
                    "自分で入力する"
                ],
                'error': False,
                'processing': False
            }
            
        except Exception as e:
            print(f"❌ 人数処理エラー: {e}")
            import traceback
            traceback.print_exc()
            return {
                'message': f'人数の処理でエラーが発生しました: {str(e)}\n'
                          'もう一度お試しください。',
                'step': 'party_size_input',
                'error': True,
                'options': ["1名", "2名", "3名", "4名", "5名", "6名", "その他"]
            }
    
    def _handle_contact_info_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """連絡先情報の処理"""
        try:
            # 連絡先情報を抽出
            contact_info = self._extract_contact_info(user_input)
            
            if not contact_info.get('name') or not contact_info.get('phone'):
                return {
                    'session_id': session_id,
                    'message': '連絡先情報を正しく理解できませんでした。\n'
                              'お名前と電話番号を教えてください。\n'
                              '例: 「田中太郎 090-1234-5678」',
                    'step': 'contact_info_input',
                    'options': [
                        "田中太郎 090-1234-5678",
                        "佐藤花子 080-9876-5432", 
                        "山田次郎 070-1111-2222",
                        "自分で入力する"
                    ],
                    'error': True,
                    'processing': False
                }
            
            session = self.reservation_sessions[session_id]
            session['data']['contact'] = contact_info
            session['step'] = 'email_input'
            
            return {
                'session_id': session_id,
                'message': f"📝 お名前: {contact_info['name']}\n"
                          f"📱 電話番号: {contact_info['phone']}\n\n"
                          f"続いて、メールアドレスを教えてください。\n"
                          f"予約確認メールの受信に必要です。",
                'step': 'email_input',
                'options': [],
                'error': False,
                'processing': False
            }
            
        except Exception as e:
            return {
                'message': f'連絡先情報の処理でエラーが発生しました: {str(e)}\n'
                          'もう一度お試しください。',
                'step': 'contact_info_input',
                'error': True
            }
    
    def _handle_email_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """メールアドレス入力の処理"""
        try:
            import re
            
            # メールアドレスの基本的な検証
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            email = user_input.strip()
            
            if not re.match(email_pattern, email):
                return {
                    'session_id': session_id,
                    'message': 'メールアドレスの形式が正しくありません。\n'
                              '正しいメールアドレスを入力してください。\n'
                              '例: example@gmail.com',
                    'step': 'email_input',
                    'error': True,
                    'processing': False
                }
            
            session = self.reservation_sessions[session_id]
            session['data']['email'] = email
            
            # 連絡先情報にメールを追加
            if 'contact' not in session['data']:
                session['data']['contact'] = {}
            session['data']['contact']['email'] = email
            
            session['step'] = 'special_requests_input'
            
            return {
                'session_id': session_id,
                'message': f"📧 メールアドレス: {email}\n\n"
                          f"最後に、特別なご要望があれば教えてください。\n"
                          f"（記念日、アレルギー、席の希望など）\n"
                          f"特にない場合は「なし」と入力してください。",
                'step': 'special_requests_input',
                'options': [
                    "なし",
                    "誕生日のお祝いです",
                    "記念日のお祝いです",
                    "静かな席をお願いします",
                    "窓際の席をお願いします",
                    "自分で入力する"
                ],
                'error': False,
                'processing': False
            }
            
        except Exception as e:
            return {
                'message': f'メールアドレスの処理でエラーが発生しました: {str(e)}\n'
                          'もう一度お試しください。',
                'step': 'email_input',
                'error': True
            }
    
    def _handle_special_requests_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """特別要望の処理"""
        try:
            session = self.reservation_sessions[session_id]
            session['data']['special_requests'] = user_input if user_input.lower() not in ['なし', 'none', ''] else None
            session['step'] = 'confirmation'
            
            # 確認画面を生成
            data = session['data']
            restaurant = session['restaurant']
            
            formatted_datetime = datetime.fromisoformat(data['datetime']).strftime('%Y年%m月%d日 %H:%M')
            special_requests_text = data.get('special_requests') or 'なし'
            
            confirmation_message = f"🎯 **予約内容の確認**\n\n" \
                                 f"🏪 **レストラン**: {restaurant.get('name', '不明')}\n" \
                                 f"📍 **住所**: {restaurant.get('address', '不明')}\n" \
                                 f"📅 **日時**: {formatted_datetime}\n" \
                                 f"👥 **人数**: {data['party_size']}名\n" \
                                 f"📝 **お名前**: {data['contact']['name']}\n" \
                                 f"📱 **電話番号**: {data['contact']['phone']}\n" \
                                 f"📧 **メール**: {data.get('email', data['contact'].get('email', '未設定'))}\n" \
                                 f"💭 **特別要望**: {special_requests_text}\n\n" \
                                 f"この内容で予約を進めますか？"
            
            return {
                'session_id': session_id,
                'message': confirmation_message,
                'step': 'confirmation',
                'options': [
                    "✅ 予約を実行する",
                    "📝 修正する", 
                    "❌ キャンセル"
                ],
                'error': False,
                'processing': False
            }
            
        except Exception as e:
            return {
                'message': f'特別要望の処理でエラーが発生しました: {str(e)}\n'
                          'もう一度お試しください。',
                'step': 'special_requests_input',
                'error': True
            }
    
    def _handle_confirmation(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """確認画面の処理"""
        try:
            user_input_lower = user_input.lower()
            print(f"📋 確認処理: ユーザー入力='{user_input}'")
            
            if '実行' in user_input or 'はい' in user_input or 'ok' in user_input_lower or 'yes' in user_input_lower or '✅' in user_input:
                print("✅ 予約実行開始")
                session = self.reservation_sessions[session_id]
                restaurant = session['restaurant']
                data = session['data']
                
                # 実際の予約処理を実行
                print("🤖 予約処理開始:")
                print(f"  レストラン: {restaurant.get('name', 'Unknown')}")
                print(f"  電話番号: {restaurant.get('phone_number', 'なし')}")
                print(f"  ウェブサイト: {restaurant.get('website', 'なし')}")
                
                # URLから予約システムを判定
                website = restaurant.get('website', '')
                print(f"🌐 ウェブサイト: {website}")
                
                if 'tabelog.com' in website:
                    # 食べログの場合
                    print("🍣 食べログでの予約を試みます")
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        booking_result = loop.run_until_complete(self._execute_tabelog_booking(restaurant, data))
                    finally:
                        loop.close()
                        
                elif 'toreta.in' in website or 'toreta-reserve' in website:
                    # Toretaの場合
                    print("🎆 Toretaでの予約を試みます")
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        booking_result = loop.run_until_complete(self._execute_toreta_booking(restaurant, data))
                    finally:
                        loop.close()
                        
                else:
                    # その他のサイトは対応していない
                    print(f"⚠️ 未対応の予約システム: {website}")
                    booking_result = {
                        'success': False,
                        'error': 'not_supported',
                        'message': '申し訳ございません。現在対応している予約システムは、食べログとToretaのみです。',
                        'website': website,
                        'supported_systems': ['食べログ (tabelog.com)', 'Toreta (toreta.in)']
                    }
                print(f"🎯 予約結果: success={booking_result.get('success')}, method={booking_result.get('method', 'unknown')}")
                
                if booking_result.get('success'):
                    session['step'] = 'completed'
                    session['booking_result'] = booking_result
                    
                    formatted_datetime = datetime.fromisoformat(data['datetime']).strftime('%Y年%m月%d日 %H:%M')
                    reservation_id = booking_result.get('reservation_id', f"RES-{session_id[-8:]}")
                    
                    # PuppeteerMCPの処理詳細を含める
                    puppeteer_steps = booking_result.get('steps_completed', [])
                    steps_text = "\n".join([f"• {step}" for step in puppeteer_steps])
                    
                    message = "🎉 **予約が完了しました！**\n\n"
                    message += f"📋 **予約番号**: {reservation_id}\n"
                    message += f"🏪 **レストラン**: {restaurant.get('name')}\n"
                    message += f"📍 **住所**: {restaurant.get('address', '不明')}\n"
                    message += f"📅 **予約日時**: {formatted_datetime}\n"
                    message += f"👥 **人数**: {data['party_size']}名\n"
                    message += f"📝 **予約者名**: {data['contact']['name']}\n"
                    message += f"📱 **連絡先**: {data['contact']['phone']}\n"
                    message += f"📧 **メール**: {data.get('email', data['contact'].get('email', '未設定'))}\n\n"
                    
                    if puppeteer_steps:
                        message += f"🤖 **AI予約処理**:\n{steps_text}\n\n"
                    
                    message += f"📞 **レストラン連絡先**: {restaurant.get('phone_number', '店舗にお問い合わせください')}\n\n"
                    message += "💡 **ご来店の際のお願い**:\n"
                    message += "• 予約時間の5-10分前にお越しください\n"
                    message += "• 遅刻やキャンセルの場合は事前にレストランにご連絡ください\n"
                    message += f"• 予約番号をお控えください: **{reservation_id}**\n\n"
                    message += "🍽️ 素敵なお食事をお楽しみください！"
                    
                    return {
                        'session_id': session_id,
                        'message': message,
                        'step': 'completed',
                        'success': True,
                        'booking_result': booking_result,
                        'error': False,
                        'processing': False,
                        'reservation_details': {
                            'reservation_id': reservation_id,
                            'restaurant_name': restaurant.get('name'),
                            'datetime': formatted_datetime,
                            'party_size': data['party_size'],
                            'contact': data['contact'],
                            'email': data.get('email'),
                            'special_requests': data.get('special_requests'),
                            'puppeteer_method': booking_result.get('method', 'unknown')
                        }
                    }
                else:
                    # エラー処理（半自動モードを含む）
                    error_message = self._create_error_message(booking_result, restaurant)
                    
                    # 半自動モードの場合は異なるオプションを提供
                    if booking_result.get('semi_automated'):
                        return {
                            'session_id': session_id,
                            'message': error_message,
                            'step': 'semi_automated',
                            'success': False,
                            'error': False,  # 半自動モードはエラーではない
                            'processing': False,
                            'browser_opened': booking_result.get('browser_opened', False),
                            'booking_info': booking_result.get('booking_info', {}),
                            'restaurant_url': booking_result.get('restaurant_url', restaurant.get('website', '')),
                            'options': [
                                "✅ ブラウザで予約を完了しました",
                                "📞 電話で予約する",
                                "🔄 別のレストランを探す"
                            ]
                        }
                    elif booking_result.get('error') == 'ai_detection':
                        # AI検出エラーの場合
                        return {
                            'session_id': session_id,
                            'message': error_message,
                            'step': 'ai_blocked',
                            'success': False,
                            'error': True,
                            'processing': False,
                            'booking_info': booking_result.get('booking_info', {}),
                            'restaurant_url': booking_result.get('restaurant_url', restaurant.get('website', '')),
                            'phone_number': booking_result.get('phone_number', restaurant.get('phone_number', '')),
                            'options': [
                                "📱 食べログサイトを開く",
                                "📞 今すぐ電話する",
                                "🔍 別のレストランを探す",
                                "💡 他の予約サイトを使う"
                            ]
                        }
                    else:
                        return {
                            'session_id': session_id,
                            'message': error_message,
                            'step': 'completed',
                            'success': False,
                            'error': True,
                            'processing': False,
                            'options': ["🔄 もう一度試す", "📞 電話予約の案内", "❌ 終了"]
                        }
                
            elif 'キャンセル' in user_input or 'cancel' in user_input_lower:
                # セッションを削除
                del self.reservation_sessions[session_id]
                return {
                    'message': "❌ 予約をキャンセルしました。\n"
                              "また機会がございましたらお気軽にお声がけください。",
                    'step': 'completed',
                    'cancelled': True
                }
                
            elif '修正' in user_input or 'edit' in user_input_lower:
                return {
                    'message': "📝 どの項目を修正しますか？",
                    'step': 'confirmation',
                    'options': [
                        "📅 日時を変更",
                        "👥 人数を変更",
                        "📝 連絡先を変更",
                        "💭 特別要望を変更",
                        "🔙 確認画面に戻る"
                    ]
                }
            elif '続行' in user_input or user_input.strip() == '':
                # 空の入力や「続行」は確認画面を再表示
                session = self.reservation_sessions[session_id]
                restaurant = session['restaurant']
                data = session['data']
                
                formatted_datetime = datetime.fromisoformat(data['datetime']).strftime('%Y年%m月%d日 %H:%M')
                special_requests_text = data.get('special_requests') or 'なし'
                
                confirmation_message = f"🎯 **予約内容の確認**\n\n" \
                                     f"🏪 **レストラン**: {restaurant.get('name', '不明')}\n" \
                                     f"📍 **住所**: {restaurant.get('address', '不明')}\n" \
                                     f"📅 **日時**: {formatted_datetime}\n" \
                                     f"👥 **人数**: {data['party_size']}名\n" \
                                     f"📝 **お名前**: {data['contact']['name']}\n" \
                                     f"📱 **電話番号**: {data['contact']['phone']}\n" \
                                     f"📧 **メール**: {data.get('email', data['contact'].get('email', '未設定'))}\n" \
                                     f"💭 **特別要望**: {special_requests_text}\n\n" \
                                     f"この内容で予約を取りますか？\n" \
                                     f"📞 予約完了後、必要に応じてレストランにお電話で確認することをお勧めします。"
                
                return {
                    'session_id': session_id,
                    'message': confirmation_message,
                    'step': 'confirmation',
                    'options': [
                        "✅ 予約を実行する",
                        "📝 修正する", 
                        "❌ キャンセル"
                    ],
                    'error': False,
                    'processing': False
                }
            else:
                return {
                    'session_id': session_id,
                    'message': "申し訳ございません。入力を理解できませんでした。\n"
                              "「予約を実行する」「修正する」「キャンセル」のいずれかを選んでください。",
                    'step': 'confirmation',
                    'options': [
                        "✅ 予約を実行する",
                        "📝 修正する", 
                        "❌ キャンセル"
                    ],
                    'error': True
                }
                
        except Exception as e:
            print(f"❌ 確認処理エラー: {e}")
            import traceback
            traceback.print_exc()
            return {
                'message': f'予約の実行中にエラーが発生しました: {str(e)}\n'
                          '申し訳ございませんが、もう一度お試しください。',
                'step': 'confirmation',
                'error': True
            }
    
    def _parse_datetime_with_ai(self, user_input: str) -> Optional[str]:
        """
        OpenAI APIを使用して自然言語から日時を抽出
        
        Args:
            user_input: ユーザーの入力
            
        Returns:
            Optional[str]: ISO形式の日時文字列 (YYYY-MM-DDTHH:MM:SS)
        """
        try:
            # OpenAI APIで日時を抽出
            now = datetime.now()
            current_date = now.strftime('%Y年%m月%d日')
            current_time = now.strftime('%H時%M分')
            
            prompt = f"""
            現在の日時: {current_date} {current_time}

            ユーザーの入力から予約日時を抽出してください。
            入力: "{user_input}"

            以下の形式で日時を返してください（ISO形式）:
            YYYY-MM-DDTHH:MM:SS

            例:
            - "明日の19時" -> 翌日の19:00:00
            - "今週土曜日の12時" -> 今週土曜日の12:00:00
            - "12月25日18時30分" -> 該当年の12月25日18:30:00

            注意:
            - 過去の日時は無効です（現在より後の日時のみ）
            - 年が指定されていない場合は、現在の年または翌年を適切に推測してください
            - 時刻が指定されていない場合は19:00をデフォルトとします

            日時のみを返してください。他の説明は不要です。
            抽出できない場合は"INVALID"と返してください。
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "あなたは日時抽出の専門家です。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=50
            )
            
            result = response.choices[0].message.content.strip()
            
            if result == "INVALID":
                return None
            
            # 結果を検証
            try:
                parsed_dt = datetime.fromisoformat(result)
                
                # 過去の日時は無効
                if parsed_dt <= now:
                    return None
                
                return result
                
            except:
                return None
                
        except Exception as e:
            print(f"❌ AI日時解析エラー: {e}")
            return None
    
    def _extract_party_size(self, user_input: str) -> Optional[int]:
        """
        ユーザー入力から人数を抽出
        
        Args:
            user_input: ユーザーの入力
            
        Returns:
            Optional[int]: 人数
        """
        try:
            print(f"🔍 人数抽出処理: '{user_input}'")
            import re
            
            # 数字を探す
            numbers = re.findall(r'\d+', user_input)
            print(f"🔢 見つかった数字: {numbers}")
            
            if numbers:
                result = int(numbers[0])
                print(f"✅ 数字から抽出: {result}")
                return result
            
            # 漢数字や文字から推定
            user_input.lower()
            
            if '一' in user_input or '1名' in user_input or '1人' in user_input:
                print("✅ 1名として認識")
                return 1
            elif '二' in user_input or '2名' in user_input or '2人' in user_input:
                print("✅ 2名として認識")
                return 2
            elif '三' in user_input or '3名' in user_input or '3人' in user_input:
                print("✅ 3名として認識")
                return 3
            elif '四' in user_input or '4名' in user_input or '4人' in user_input:
                print("✅ 4名として認識")
                return 4
            elif '五' in user_input or '5名' in user_input or '5人' in user_input:
                print("✅ 5名として認識")
                return 5
            elif '六' in user_input or '6名' in user_input or '6人' in user_input:
                print("✅ 6名として認識")
                return 6
            
            print("❌ 人数を抽出できませんでした")
            return None
            
        except Exception as e:
            print(f"❌ 人数抽出エラー: {e}")
            return None
    
    def _extract_contact_info(self, user_input: str) -> Dict[str, str]:
        """
        ユーザー入力から連絡先情報を抽出
        
        Args:
            user_input: ユーザーの入力
            
        Returns:
            Dict[str, str]: 連絡先情報
        """
        try:
            import re
            
            # 電話番号のパターン
            phone_patterns = [
                r'0[789]0-?\d{4}-?\d{4}',  # 携帯電話
                r'0\d{1,4}-?\d{1,4}-?\d{4}',  # 固定電話
                r'\d{10,11}'  # 数字のみ
            ]
            
            phone = None
            for pattern in phone_patterns:
                match = re.search(pattern, user_input)
                if match:
                    phone = match.group()
                    break
            
            # 名前を抽出（電話番号以外の部分）
            name = user_input
            if phone:
                name = user_input.replace(phone, '').strip()
            
            # 句読点やスペースで分割して、名前らしい部分を探す
            name_parts = re.split(r'[、,\s]+', name)
            name = ' '.join([part for part in name_parts if part and not part.isdigit()])
            
            result = {
                'name': name.strip(),
                'phone': phone.strip() if phone else ''
            }
            
            print(f"📋 連絡先抽出結果: {result}")
            return result
            
        except Exception as e:
            print(f"❌ 連絡先抽出エラー: {e}")
            return {'name': '', 'phone': ''}
    
    def _handle_bulk_form_data(self, session_id: str, form_data: str) -> Dict[str, Any]:
        """一括フォームデータの処理"""
        print("📝 一括フォームデータ処理開始")
        print(f"📥 受信データ（全文）: '{form_data}'")
        try:
            # データを解析
            import re
            
            # 日時を抽出 - より柔軟なパターン
            datetime_match = re.search(r'日時:\s*([0-9-]+)\s+([0-9:]+)', form_data)
            party_size_match = re.search(r'人数:\s*(\d+)名', form_data)
            name_match = re.search(r'名前:\s*([^,]+)', form_data)
            phone_match = re.search(r'電話:\s*([^,]+)', form_data)
            email_match = re.search(r'メール:\s*([^,]+)', form_data)
            requests_match = re.search(r'要望:\s*(.+?)(?:$|,)', form_data)
            
            print("🔍 正規表現マッチ結果:")
            print(f"  datetime_match: {datetime_match.groups() if datetime_match else None}")
            print(f"  party_size_match: {party_size_match.groups() if party_size_match else None}")
            print(f"  name_match: {name_match.groups() if name_match else None}")
            print(f"  phone_match: {phone_match.groups() if phone_match else None}")
            print(f"  email_match: {email_match.groups() if email_match else None}")
            print(f"  requests_match: {requests_match.groups() if requests_match else None}")
            
            missing_fields = []
            if not datetime_match:
                missing_fields.append("日時")
            if not party_size_match:
                missing_fields.append("人数")
            if not name_match:
                missing_fields.append("名前")
            if not phone_match:
                missing_fields.append("電話番号")
            if not email_match:
                missing_fields.append("メールアドレス")
            
            if missing_fields:
                print(f"❌ 不足フィールド: {missing_fields}")
                return {
                    'session_id': session_id,
                    'message': f'以下の情報が不足しています: {", ".join(missing_fields)}\n'
                              f'もう一度入力してください。',
                    'step': 'datetime_input',
                    'error': True
                }
            
            # 日時をISO形式に変換
            date_str = datetime_match.group(1)
            time_str = datetime_match.group(2)
            iso_datetime = f"{date_str}T{time_str}:00"
            
            # セッションデータを設定
            session = self.reservation_sessions[session_id]
            session['data'] = {
                'datetime': iso_datetime,
                'party_size': int(party_size_match.group(1)),
                'contact': {
                    'name': name_match.group(1).strip(),
                    'phone': phone_match.group(1).strip(),
                    'email': email_match.group(1).strip() if email_match else ''
                },
                'email': email_match.group(1).strip() if email_match else '',
                'special_requests': requests_match.group(1).strip() if requests_match and requests_match.group(1).strip() != 'なし' else None
            }
            session['step'] = 'confirmation'
            
            # 確認画面を生成
            data = session['data']
            restaurant = session['restaurant']
            
            formatted_datetime = datetime.fromisoformat(iso_datetime).strftime('%Y年%m月%d日 %H:%M')
            party_size = data['party_size']
            name = data['contact']['name']
            phone = data['contact']['phone']
            email = data.get('email', '')
            special_requests_text = data.get('special_requests') or 'なし'
            
            confirmation_message = f"🎯 **予約内容の確認**\n\n" \
                                 f"🏪 **レストラン**: {restaurant.get('name', '不明')}\n" \
                                 f"📍 **住所**: {restaurant.get('address', '不明')}\n" \
                                 f"📅 **日時**: {formatted_datetime}\n" \
                                 f"👥 **人数**: {party_size}名\n" \
                                 f"📝 **お名前**: {name}\n" \
                                 f"📱 **電話番号**: {phone}\n" \
                                 f"📧 **メール**: {email}\n" \
                                 f"💭 **特別要望**: {special_requests_text}\n\n" \
                                 f"この内容で予約を取りますか？\n" \
                                 f"📞 予約完了後、必要に応じてレストランにお電話で確認することをお勧めします。"
            
            print("✅ 一括データ処理完了、確認画面へ")
            return {
                'session_id': session_id,
                'message': confirmation_message,
                'step': 'confirmation',
                'options': [
                    "✅ 予約を実行する",
                    "📝 修正する", 
                    "❌ キャンセル"
                ],
                'error': False,
                'processing': False
            }
            
        except Exception as e:
            print(f"❌ 一括フォームデータ処理エラー: {e}")
            import traceback
            traceback.print_exc()
            return {
                'session_id': session_id,
                'message': f'データ処理中にエラーが発生しました: {str(e)}',
                'step': 'datetime_input',
                'error': True
            }
    
    async def _execute_toreta_booking(self, restaurant: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Toreta経由での予約を実行
        """
        try:
            print("🤖 Toreta予約を開始します")
            
            # 日時を解析
            datetime_obj = datetime.fromisoformat(data['datetime'])
            reservation_date = datetime_obj.strftime('%Y-%m-%d')
            reservation_time = datetime_obj.strftime('%H:%M')
            
            # 顧客情報を準備
            customer_info = {
                'name': data['contact']['name'],
                'phone': data['contact']['phone'],
                'email': data.get('email', data['contact'].get('email', '')),
                'special_requests': data.get('special_requests', '')
            }
            
            # Toreta予約を実行
            result = await toreta_service.make_reservation(
                restaurant_url=restaurant.get('website', ''),
                reservation_date=reservation_date,
                reservation_time=reservation_time,
                party_size=data['party_size'],
                customer_info=customer_info
            )
            
            print(f"✅ Toreta予約結果: {result}")
            return result
            
        except Exception as e:
            print(f"❌ Toreta予約エラー: {e}")
            return {
                'success': False,
                'error': 'toreta_error',
                'message': f'Toreta予約中にエラーが発生しました: {str(e)}'
            }
    
    async def _execute_tabelog_booking(self, restaurant: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """
        食べログで実際に予約を実行
        
        Args:
            restaurant: レストラン情報（食べログURLを含む）
            data: 予約データ
            
        Returns:
            Dict[str, Any]: 予約結果
        """
        try:
            website = restaurant.get('website', '')
            
            # 食べログURLでない場合はエラー
            if 'tabelog.com' not in website:
                return {
                    'success': False,
                    'error': 'not_tabelog',
                    'message': 'このレストランは食べログ以外のサイトです'
                }
            
            # 日時を分割
            datetime_obj = datetime.fromisoformat(data['datetime'])
            date_str = datetime_obj.strftime('%Y-%m-%d')
            time_str = datetime_obj.strftime('%H:%M')
            
            # 食べログ予約を実行
            result = await tabelog_service.make_reservation(
                restaurant_url=website,
                reservation_date=date_str,
                reservation_time=time_str,
                party_size=data['party_size'],
                customer_info={
                    'name': data['contact']['name'],
                    'phone': data['contact']['phone'],
                    'email': data['contact'].get('email', '')
                }
            )
            
            if result['success']:
                return {
                    'success': True,
                    'reservation_id': result.get('reservation_id'),
                    'method': 'tabelog_booking',
                    'steps_completed': [
                        '🌐 食べログにアクセス中...',
                        '📅 希望日時を選択中...',
                        '👥 人数を設定中...',
                        '📝 お客様情報を入力中...',
                        '✅ 予約内容を確認中...',
                        '🎉 予約が完了しました！'
                    ],
                    'restaurant_name': restaurant.get('name'),
                    'booking_details': {
                        'datetime': data['datetime'],
                        'party_size': data['party_size'],
                        'contact': data['contact'],
                        'special_requests': data.get('special_requests')
                    }
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', '予約失敗'),
                    'message': result.get('message', '予約を完了できませんでした'),
                    'alternative': result.get('alternative')
                }
                
        except Exception as e:
            print(f"❌ 食べログ予約エラー: {str(e)}")
            return {
                'success': False,
                'error': 'exception',
                'message': f'予約処理中にエラーが発生しました: {str(e)}'
            }
    
    def _create_error_message(self, booking_result: Dict[str, Any], restaurant: Dict[str, Any]) -> str:
        """
        エラーメッセージを生成
        """
        error_type = booking_result.get('error', 'unknown')
        
        # 半自動モードの場合
        if booking_result.get('semi_automated'):
            instructions = booking_result.get('instructions', [])
            instructions_text = '\n'.join(instructions)
            booking_info = booking_result.get('booking_info', {})
            
            if booking_result.get('browser_opened'):
                return (
                    f"🌐 **ブラウザウィンドウを開きました**\n\n"
                    f"⚠️ **食べログのセキュリティにより、手動での予約完了が必要です**\n\n"
                    f"📌 **現在の状態**:\n"
                    f"✅ 別ウィンドウでブラウザが開いています\n"
                    f"✅ レストランページを表示中\n"
                    f"⚠️ 予約情報の自動入力を試みましたが、手動確認が必要です\n\n"
                    f"📝 **予約したい内容**:\n"
                    f"• 日付: **{booking_info.get('date', '未設定')}**\n"
                    f"• 時間: **{booking_info.get('time', '未設定')}**\n"
                    f"• 人数: **{booking_info.get('party_size', '未設定')}名**\n"
                    f"• お名前: **{booking_info.get('customer_name', '未設定')}**\n\n"
                    f"📋 **ブラウザでの手順**:\n{instructions_text}\n\n"
                    f"💡 予約完了後、食べログから確認メールが届きます"
                )
            elif booking_result.get('manual_booking_required'):
                phone_number = booking_result.get('phone_number', '店舗にお問い合わせください')
                return (
                    f"⚠️ **食べログの自動予約防止機能により、手動での予約が必要です**\n\n"
                    f"🚫 **理由**: {booking_result.get('message', 'AI検出により自動予約がブロックされました')}\n\n"
                    f"📌 **代替の予約方法**:\n\n"
                    f"🌐 **ブラウザで直接予約**:\n"
                    f"1. 食べログのサイト: {booking_result.get('restaurant_url', restaurant.get('website', ''))}\n"
                    f"2. 「空席確認・予約」ボタンをクリック\n"
                    f"3. 以下の情報で予約:\n"
                    f"   • 日付: {booking_info.get('date', '希望日')}\n"
                    f"   • 時間: {booking_info.get('time', '希望時間')}\n"
                    f"   • 人数: {booking_info.get('party_size', '希望人数')}名\n\n"
                    f"📞 **または電話予約**: {phone_number}\n\n"
                    f"💡 申し訳ございません。食べログのセキュリティ強化により、完全自動予約は制限されています。"
                )
        
        if error_type == 'ai_detection':
            # AI検出エラーの場合
            phone_number = booking_result.get('phone_number', restaurant.get('phone_number', '店舗にお問い合わせください'))
            booking_info = booking_result.get('booking_info', {})
            restaurant_url = booking_result.get('restaurant_url', restaurant.get('website', ''))
            
            return (
                f"⚠️ **食べログのセキュリティにより自動予約がブロックされました**\n\n"
                f"食べログは不正な自動予約を防ぐため、AI検出システムを導入しています。\n"
                f"申し訳ございませんが、以下の方法で予約をお願いします。\n\n"
                f"📱 **オプション1: 食べログで予約（1分で完了）**\n"
                f"準備した予約情報:\n"
                f"📅 日付: **{booking_info.get('date', '未設定')}**\n"
                f"⏰ 時間: **{booking_info.get('time', '未設定')}**\n"
                f"👥 人数: **{booking_info.get('party_size', '未設定')}名**\n"
                f"📝 お名前: **{booking_info.get('customer_name', '未設定')}**\n\n"
                f"👉 [**食べログで予約する**]({restaurant_url})\n"
                f"（クリックして上記情報で予約を完了してください）\n\n"
                f"---\n\n"
                f"📞 **オプション2: 電話予約（最も確実）**\n"
                f"📱 **{phone_number}**\n"
                f"「{booking_info.get('date', '')}の{booking_info.get('time', '')}に"
                f"{booking_info.get('party_size', '')}名で予約したいです」\n\n"
                f"💡 **なぜ自動予約ができないか？**\n"
                f"食べログは転売防止のため、AIによる予約を制限しています。\n"
                f"これはレストランと利用者を守るための措置です。"
            )
        elif error_type == 'not_supported':
            # 食べログ以外のサイトの場合
            website = booking_result.get('website', 'なし')
            if website != 'なし' and website:
                domain = website.split('/')[2] if '/' in website else website
                return (
                    f"⚠️ **このレストランのオンライン予約には対応していません**\n\n"
                    f"🚫 **非対応サイト**: {domain}\n\n"
                    f"📌 **現在の対応状況**:\n"
                    f"• ✅ 食べログ（tabelog.com）のみ対応\n"
                    f"• ❌ その他のサイト（ぐるなび、ホットペッパーなど）は非対応\n\n"
                    f"🔄 **代替の予約方法**:\n\n"
                    f"📞 **直接お電話（推奨）**: {restaurant.get('phone_number', '店舗にお問い合わせください')}\n"
                    f"• 確実に予約が取れます\n"
                    f"• 詳細な要望もお伝えできます\n\n"
                    f"🌐 **レストランのサイトで直接予約**: {website}\n\n"
                    f"💡 **ヒント**: 食べログに掲載されているレストランをお選びいただければ、AI予約が可能です"
                )
            else:
                return (
                    f"⚠️ **このレストランのオンライン予約には対応していません**\n\n"
                    f"📌 **現在の対応状況**:\n"
                    f"• ✅ 食べログ（tabelog.com）のみ対応\n"
                    f"• ❌ その他のサイトは非対応\n\n"
                    f"🔄 **代替の予約方法**:\n\n"
                    f"📞 **直接お電話（推奨）**: {restaurant.get('phone_number', '店舗にお問い合わせください')}\n"
                    f"• 確実に予約が取れます\n"
                    f"• 詳細な要望もお伝えできます\n\n"
                    f"💡 **ヒント**: 食べログに掲載されているレストランをお選びいただければ、AI予約が可能です"
                )
        elif error_type == 'not_tabelog':
            return (
                f"⚠️ **食べログ以外のサイトには対応していません**\n\n"
                f"📌 このシステムは食べログ専用です\n\n"
                f"🔄 **代替の予約方法**:\n\n"
                f"📞 **直接お電話**: {restaurant.get('phone_number', '店舗にお問い合わせください')}\n\n"
                f"💡 食べログに掲載されているレストランをお選びください"
            )
        else:
            # その他のエラー
            return (
                f"⚠️ **オンライン予約を完了できませんでした**\n\n"
                f"状況: {booking_result.get('message', booking_result.get('error', '不明なエラー'))}\n\n"
                f"🔄 **代替の予約方法をご利用ください:**\n\n"
                f"📞 **直接お電話（推奨）**: {restaurant.get('phone_number', '店舗にお問い合わせください')}\n"
                f"• 確実に予約が取れます\n"
                f"• 詳細な要望もお伝えできます\n\n"
                f"🌐 **予約サイト**: 食べログで直接予約\n\n"
                f"🚶 **直接来店**: 空席がある場合はご案内可能です"
            )
    
    def _execute_booking_with_puppeteer(self, restaurant: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Puppeteerを使用した実際の予約処理（現在は使用していません）
        """
        # 食べログ以外は対応していない
        return {
            'success': False,
            'error': 'not_supported',
            'message': '食べログ以外のサイトには対応していません'
        }
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """セッションの状態を取得"""
        if session_id not in self.reservation_sessions:
            return {'error': 'セッションが見つかりません'}
        
        session = self.reservation_sessions[session_id]
        return {
            'step': session['step'],
            'data': session['data'],
            'restaurant': session['restaurant']
        }
    
    def cancel_session(self, session_id: str) -> Dict[str, Any]:
        """セッションをキャンセル"""
        if session_id in self.reservation_sessions:
            del self.reservation_sessions[session_id]
            return {'message': '予約セッションをキャンセルしました'}
        return {'error': 'セッションが見つかりません'}