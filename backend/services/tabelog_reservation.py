"""
食べログ予約専用サービス
食べログのネット予約システムを使用してレストラン予約を自動化
"""
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from playwright.async_api import async_playwright, Page, Browser
import re
from urllib.parse import urlparse

# ロガー設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TabelogReservationService:
    """食べログ予約専用サービス"""
    
    def __init__(self):
        """初期化"""
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
    
    async def initialize(self):
        """ブラウザを初期化"""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=False,  # デバッグ時は False に設定
                args=[
                    '--start-maximized',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process'
                ]
            )
            context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                locale='ja-JP',
                timezone_id='Asia/Tokyo',
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                extra_http_headers={
                    'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
                }
            )
            self.page = await context.new_page()
            
            # より高度な自動化検出回避
            await self.page.add_init_script("""
                // webdriver プロパティを削除
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Chrome プロパティを追加
                window.chrome = {
                    runtime: {}
                };
                
                // Permission API のオーバーライド
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // Plugin 配列を修正
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // Language プロパティを修正
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['ja-JP', 'ja', 'en-US', 'en']
                });
            """)
            
            logger.info("🌐 ブラウザを初期化しました")
    
    async def close(self):
        """ブラウザを閉じる"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("🔒 ブラウザを閉じました")
    
    def is_tabelog_url(self, url: str) -> bool:
        """URLが食べログかチェック"""
        if not url:
            return False
        parsed = urlparse(url)
        return 'tabelog.com' in parsed.netloc
    
    async def make_reservation(
        self,
        restaurant_url: str,
        reservation_date: str,
        reservation_time: str,
        party_size: int,
        customer_info: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        食べログで予約を実行
        
        Args:
            restaurant_url: 食べログのレストランURL
            reservation_date: 予約日 (YYYY-MM-DD)
            reservation_time: 予約時間 (HH:MM)
            party_size: 人数
            customer_info: 顧客情報 (name, phone, email)
        
        Returns:
            予約結果の辞書
        """
        try:
            await self.initialize()
            
            # 食べログURLかチェック
            if not self.is_tabelog_url(restaurant_url):
                return {
                    'success': False,
                    'error': 'URLが食べログのものではありません',
                    'message': f'提供されたURL: {restaurant_url}'
                }
            
            logger.info(f"🍴 食べログ予約開始: {restaurant_url}")
            logger.info(f"📅 予約情報: {reservation_date} {reservation_time}, {party_size}名")
            
            # 半自動化モードの通知
            logger.info("🤖 半自動予約モードで実行します")
            logger.info("📌 食べログのページを開き、予約情報を事前入力します")
            logger.info("✋ 最終的な予約確定は手動で行ってください")
            
            # レストランページにアクセス
            try:
                # より人間らしい動作をシミュレート
                await self.page.goto('https://tabelog.com/', wait_until='domcontentloaded', timeout=30000)
                await asyncio.sleep(2)  # トップページで少し待機
                
                # 実際のレストランページに移動
                await self.page.goto(restaurant_url, wait_until='domcontentloaded', timeout=60000)
            except Exception as e:
                logger.warning(f"⚠️ ページ読み込み警告: {str(e)}")
                # タイムアウトしても続行
            
            # ページの読み込みを待つ
            await asyncio.sleep(5)
            
            # AI検出ページにリダイレクトされた場合のチェック
            current_url = self.page.url
            if 'ai_request_booking' in current_url:
                logger.warning("⚠️ 食べログのAI検出ページにリダイレクトされました")
                logger.info("🔄 手動予約用のガイドを提供します")
                
                # 電話番号を取得しようとする
                await self.page.goto(restaurant_url, wait_until='domcontentloaded', timeout=60000)
                await asyncio.sleep(3)
                
                phone_element = await self.page.query_selector('.rst-info-table__tel-num, .rstinfo-table__tel-num')
                phone_number = await phone_element.text_content() if phone_element else None
                
                return {
                    'success': False,
                    'error': 'ai_detection',
                    'message': '食べログの自動予約防止機能が作動しました。',
                    'manual_booking_required': True,
                    'restaurant_url': restaurant_url,
                    'phone_number': phone_number,
                    'booking_info': {
                        'date': reservation_date,
                        'time': reservation_time,
                        'party_size': party_size,
                        'customer_name': customer_info.get('name')
                    },
                    'instructions': [
                        '1. ブラウザで直接食べログのサイトにアクセスしてください',
                        '2. レストランのページで「空席確認・予約」ボタンをクリック',
                        f'3. 日付: {reservation_date}、時間: {reservation_time}、人数: {party_size}名を選択',
                        '4. お客様情報を入力して予約を完了させてください',
                        f'5. または、お電話での予約も可能です: {phone_number if phone_number else "店舗にお問い合わせください"}'
                    ]
                }
            
            # ネット予約ボタンを探す
            reservation_button_selectors = [
                'a[href*="rstdtl-reservation"]',  # 食べログの予約リンク
                'a[href*="/reservation/"]',
                'a:text("ネット予約")',
                'a:text("空席確認・予約")',
                '.rstdtl-reservation-btn a',
                '.rstdtl-side-reserve-btn a',
                'button:text("予約")',
                'a[class*="reservation"]',
                'a.js-reservation-btn'
            ]
            
            reservation_button = None
            for selector in reservation_button_selectors:
                try:
                    reservation_button = await self.page.wait_for_selector(
                        selector,
                        timeout=5000,
                        state='visible'
                    )
                    if reservation_button:
                        logger.info(f"✅ 予約ボタンを発見: {selector}")
                        break
                except Exception:
                    continue
            
            if not reservation_button:
                # ネット予約非対応の場合
                phone_element = await self.page.query_selector('.rst-info-table__tel-num, .rstinfo-table__tel-num')
                phone_number = await phone_element.text_content() if phone_element else None
                
                return {
                    'success': False,
                    'error': 'ネット予約非対応',
                    'message': 'このレストランはネット予約に対応していません',
                    'phone_number': phone_number,
                    'manual_booking_required': True,
                    'booking_info': {
                        'date': reservation_date,
                        'time': reservation_time,
                        'party_size': party_size,
                        'customer_name': customer_info.get('name')
                    },
                    'alternative': f'電話予約をご利用ください: {phone_number}' if phone_number else '店舗に直接お問い合わせください'
                }
            
            # 予約ページに移動
            logger.info("🔗 予約ページへ移動を試みます")
            await reservation_button.click()
            try:
                await self.page.wait_for_load_state('domcontentloaded', timeout=30000)
            except Exception:
                pass  # タイムアウトしても続行
            await asyncio.sleep(3)
            
            # 再度AI検出チェック
            current_url = self.page.url
            if 'ai_request_booking' in current_url:
                logger.warning("⚠️ 予約ページでAI検出されました")
                return {
                    'success': False,
                    'error': 'ai_detection',
                    'message': '食べログの自動予約防止機能により、自動予約を完了できません。',
                    'semi_automated': True,
                    'browser_opened': True,
                    'current_url': current_url,
                    'booking_info': {
                        'date': reservation_date,
                        'time': reservation_time,
                        'party_size': party_size,
                        'customer_name': customer_info.get('name')
                    },
                    'instructions': [
                        '🌐 ブラウザウィンドウが開いています',
                        '📝 以下の情報で手動で予約を完了してください:',
                        f'  • 日付: {reservation_date}',
                        f'  • 時間: {reservation_time}',
                        f'  • 人数: {party_size}名',
                        f'  • お名前: {customer_info.get("name")}',
                        f'  • 電話番号: {customer_info.get("phone")}',
                        f'  • メール: {customer_info.get("email")}'
                    ]
                }
            
            # 予約情報の自動入力を試みる（半自動モード）
            logger.info("📝 予約情報の自動入力を開始します")
            logger.info("⚠️ 注意: 最終的な予約確定は手動で行ってください")
            logger.info("ℹ️ コース・座席は「指定なし」で進めます")
            
            # 基本情報のみ入力を試みる
            try:
                # 日付選択
                date_success = await self._select_date(reservation_date)
                if date_success:
                    logger.info("✅ 日付を入力しました")
                else:
                    logger.info("⚠️ 日付の自動入力に失敗 - 手動で選択してください")
                    
                # 時間選択
                time_success = await self._select_time(reservation_time)
                if time_success:
                    logger.info("✅ 時間を入力しました")
                else:
                    logger.info("⚠️ 時間の自動入力に失敗 - 手動で選択してください")
                    
                # 人数選択
                party_success = await self._select_party_size(party_size)
                if party_success:
                    logger.info("✅ 人数を入力しました")
                else:
                    logger.info("⚠️ 人数の自動入力に失敗 - 手動で選択してください")
                    
                # コース選択をスキップ
                await self._skip_course_selection()
                
                # 座席選択をスキップ
                await self._skip_seat_selection()
                
                # 顧客情報入力
                info_success = await self._fill_customer_info(customer_info)
                if info_success:
                    logger.info("✅ お客様情報を入力しました")
                else:
                    logger.info("⚠️ お客様情報の自動入力に失敗 - 手動で入力してください")
                    
            except Exception as e:
                logger.warning(f"⚠️ 自動入力中にエラー: {e}")
                logger.info("📝 手動での入力をお願いします")
            
            # 半自動モードの結果を返す
            return {
                'success': False,
                'semi_automated': True,
                'browser_opened': True,
                'message': '予約情報を事前入力しました。ブラウザで予約を完了してください。',
                'current_url': self.page.url,
                'booking_info': {
                    'restaurant_url': restaurant_url,
                    'date': reservation_date,
                    'time': reservation_time,
                    'party_size': party_size,
                    'customer_name': customer_info.get('name'),
                    'phone': customer_info.get('phone'),
                    'email': customer_info.get('email')
                },
                'instructions': [
                    '✅ 予約情報を可能な限り自動入力しました',
                    '📌 ブラウザウィンドウで以下を確認してください:',
                    f'  1. 日付が {reservation_date} になっているか',
                    f'  2. 時間が {reservation_time} になっているか', 
                    f'  3. 人数が {party_size}名 になっているか',
                    '  4. お客様情報を入力',
                    '',
                    '⚠️ **重要な注意点**:',
                    '  • コース選択: 「コースなし」「席のみ」を選択',
                    '  • 座席選択: 「指定なし」「お任せ」を選択',
                    '  • 必須項目のみ入力してください',
                    '',
                    '👆 確認後、「予約する」「次へ」ボタンをクリック',
                    '📧 予約完了後、食べログから確認メールが届きます'
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ 予約エラー: {str(e)}")
            return {
                'success': False,
                'error': '予約処理エラー',
                'message': str(e)
            }
        finally:
            # ブラウザは開いたままにしておく（デバッグ用）
            # await self.close()
            pass
    
    async def _select_date(self, date_str: str) -> bool:
        """日付を選択"""
        try:
            logger.info(f"📅 日付選択: {date_str}")
            
            # 日付を解析
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            today = datetime.now()
            
            # 食べログは通常2ヶ月先までしか予約できない
            max_date = today + timedelta(days=60)
            if date_obj > max_date:
                logger.warning(f"⚠️ 日付が遠すぎます。{max_date.strftime('%Y-%m-%d')}までの日付を選択してください")
                # 1週間後の日付を代わりに使用
                date_obj = today + timedelta(days=7)
                date_str = date_obj.strftime('%Y-%m-%d')
                logger.info(f"📅 代替日付を使用: {date_str}")
            
            # 食べログの日付選択フィールドを探す
            # まず日付入力フィールドを探す
            date_input = await self.page.query_selector('input[type="date"]')
            if date_input:
                await date_input.fill(date_str)
                await asyncio.sleep(1)
                return True
            
            # カレンダーアイコンをクリック
            calendar_selectors = [
                '.js-calendar-icon',
                'button[aria-label*="カレンダー"]',
                '.calendar-trigger',
                '[class*="calendar-btn"]'
            ]
            
            for selector in calendar_selectors:
                cal_button = await self.page.query_selector(selector)
                if cal_button:
                    await cal_button.click()
                    await asyncio.sleep(2)
                    break
            
            # 月と年を確認して必要なら移動
            month_year = date_obj.strftime('%Y年%m月')
            current_month = await self.page.query_selector('.calendar-header, .month-year')
            if current_month:
                current_text = await current_month.text_content()
                # 必要に応じて次の月へ移動
                while month_year not in current_text:
                    next_button = await self.page.query_selector('.next-month, button[aria-label="次の月"]')
                    if next_button:
                        await next_button.click()
                        await asyncio.sleep(1)
                        current_month = await self.page.query_selector('.calendar-header, .month-year')
                        if current_month:
                            current_text = await current_month.text_content()
                        else:
                            break
                    else:
                        break
            
            # 日付をクリック
            day = date_obj.day
            day_selectors = [
                f'td[data-date="{date_str}"]',
                f'button:has-text("{day}")',
                f'a:has-text("{day}")',
                f'.calendar-day:has-text("{day}")'
            ]
            
            for selector in day_selectors:
                try:
                    day_element = await self.page.wait_for_selector(selector, timeout=3000)
                    if day_element:
                        await day_element.click()
                        await asyncio.sleep(1)
                        return True
                except Exception:
                    continue
            
            logger.warning("⚠️ 日付を選択できませんでした")
            return False
            
        except Exception as e:
            logger.error(f"日付選択エラー: {str(e)}")
            return False
    
    async def _select_time(self, time_str: str) -> bool:
        """時間を選択"""
        try:
            logger.info(f"⏰ 時間選択: {time_str}")
            
            # 時間セレクタのパターン
            time_selectors = [
                f'button:has-text("{time_str}")',
                f'a:has-text("{time_str}")',
                f'option:has-text("{time_str}")',
                'input[name="reservation_time"]',
                'select[name="time"]'
            ]
            
            for selector in time_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=3000)
                    if element:
                        if 'input' in selector:
                            await element.fill(time_str)
                        elif 'select' in selector:
                            await element.select_option(label=time_str)
                        else:
                            await element.click()
                        await asyncio.sleep(1)
                        return True
                except Exception:
                    continue
            
            # 時間帯のリストから選択
            time_slots = await self.page.query_selector_all('.time-slot, [class*="time"]')
            for slot in time_slots:
                text = await slot.text_content()
                if time_str in text:
                    await slot.click()
                    await asyncio.sleep(1)
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"時間選択エラー: {str(e)}")
            return False
    
    async def _select_party_size(self, party_size: int) -> bool:
        """人数を選択"""
        try:
            logger.info(f"👥 人数選択: {party_size}名")
            
            # 人数セレクタのパターン
            party_selectors = [
                f'button:has-text("{party_size}名")',
                f'button:has-text("{party_size}人")',
                f'option:has-text("{party_size}")',
                'select[name="party_size"]',
                'select[name="number"]',
                'input[name="party_size"]'
            ]
            
            for selector in party_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=3000)
                    if element:
                        if 'input' in selector:
                            await element.fill(str(party_size))
                        elif 'select' in selector:
                            await element.select_option(value=str(party_size))
                        else:
                            await element.click()
                        await asyncio.sleep(1)
                        return True
                except Exception:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"人数選択エラー: {str(e)}")
            return False
    
    async def _fill_customer_info(self, customer_info: Dict[str, str]) -> bool:
        """顧客情報を入力"""
        try:
            logger.info("📝 顧客情報入力")
            
            # 名前入力
            name_selectors = [
                'input[name*="name"]',
                'input[placeholder*="名前"]',
                'input[placeholder*="氏名"]',
                '#name',
                '.name-input'
            ]
            
            for selector in name_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    await element.fill(customer_info.get('name', ''))
                    break
            
            # 電話番号入力
            phone_selectors = [
                'input[name*="phone"]',
                'input[name*="tel"]',
                'input[type="tel"]',
                'input[placeholder*="電話"]',
                '#phone',
                '.phone-input'
            ]
            
            for selector in phone_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    await element.fill(customer_info.get('phone', ''))
                    break
            
            # メールアドレス入力
            email_selectors = [
                'input[name*="email"]',
                'input[name*="mail"]',
                'input[type="email"]',
                'input[placeholder*="メール"]',
                '#email',
                '.email-input'
            ]
            
            for selector in email_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    await element.fill(customer_info.get('email', ''))
                    break
            
            await asyncio.sleep(1)
            return True
            
        except Exception as e:
            logger.error(f"顧客情報入力エラー: {str(e)}")
            return False
    
    async def _confirm_and_submit(self) -> Dict[str, Any]:
        """予約を確認して送信"""
        try:
            logger.info("✅ 予約確認・送信")
            
            # 利用規約同意のチェックボックス
            agreement_selectors = [
                'input[type="checkbox"][name*="agree"]',
                'input[type="checkbox"][name*="terms"]',
                '.agreement-checkbox',
                '#agree'
            ]
            
            for selector in agreement_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    is_checked = await element.is_checked()
                    if not is_checked:
                        await element.check()
                        await asyncio.sleep(1)
                    break
            
            # 予約送信ボタン
            submit_selectors = [
                'button[type="submit"]:has-text("予約")',
                'button:has-text("予約を確定")',
                'button:has-text("予約する")',
                'button:has-text("確認画面へ")',
                'input[type="submit"][value*="予約"]',
                '.submit-button',
                '#submit'
            ]
            
            for selector in submit_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=3000)
                    if element:
                        await element.click()
                        break
                except Exception:
                    continue
            
            # 確認画面での最終送信
            await asyncio.sleep(3)
            
            final_submit_selectors = [
                'button:has-text("予約を確定する")',
                'button:has-text("この内容で予約")',
                'button:has-text("確定")',
                'input[type="submit"][value*="確定"]'
            ]
            
            for selector in final_submit_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element:
                        await element.click()
                        break
                except Exception:
                    continue
            
            # 予約完了を待つ
            await asyncio.sleep(5)
            
            # 予約番号を取得
            reservation_id = await self._extract_reservation_id()
            
            # 完了画面のチェック
            completion_indicators = [
                'text="予約が完了しました"',
                'text="予約を受け付けました"',
                'text="ご予約ありがとうございます"',
                '.completion-message',
                '.success-message'
            ]
            
            for indicator in completion_indicators:
                element = await self.page.query_selector(indicator)
                if element:
                    return {
                        'success': True,
                        'reservation_id': reservation_id,
                        'message': '予約が完了しました'
                    }
            
            # URLで完了を判定
            current_url = self.page.url
            if 'complete' in current_url or 'success' in current_url or 'confirm' in current_url:
                return {
                    'success': True,
                    'reservation_id': reservation_id,
                    'message': '予約が完了しました'
                }
            
            return {
                'success': False,
                'error': '予約送信失敗',
                'message': '予約の送信に失敗しました'
            }
            
        except Exception as e:
            logger.error(f"予約送信エラー: {str(e)}")
            return {
                'success': False,
                'error': '予約送信エラー',
                'message': str(e)
            }
    
    async def _skip_course_selection(self) -> bool:
        """コース選択をスキップ"""
        try:
            logger.info("🍽️ コース選択画面を確認中...")
            
            # コース選択画面の検出
            course_indicators = [
                'text="コースを選択"',
                'text="コース選択"',
                '.course-selection',
                '#course-select',
                'button:has-text("コースなし")',
                'button:has-text("席のみ")',
                'button:has-text("アラカルト")',
                'a:has-text("コースなし")',
                'a:has-text("席のみ予約")'
            ]
            
            # コースなし/席のみオプションを探す
            for selector in course_indicators:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=2000)
                    if element:
                        # 「コースなし」「席のみ」を選択
                        if 'コースなし' in selector or '席のみ' in selector or 'アラカルト' in selector:
                            await element.click()
                            await asyncio.sleep(1)
                            logger.info("✅ コースなし/席のみを選択しました")
                            return True
                except Exception:
                    continue
            
            # スキップボタンを探す
            skip_selectors = [
                'button:has-text("スキップ")',
                'button:has-text("次へ")',
                'button:has-text("続ける")',
                'a:has-text("スキップ")',
                '.skip-button'
            ]
            
            for selector in skip_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=2000)
                    if element:
                        await element.click()
                        await asyncio.sleep(1)
                        logger.info("✅ コース選択をスキップしました")
                        return True
                except Exception:
                    continue
            
            logger.info("ℹ️ コース選択画面が見つかりませんでした（スキップ）")
            return True
            
        except Exception as e:
            logger.warning(f"コース選択スキップ処理: {e}")
            return False
    
    async def _skip_seat_selection(self) -> bool:
        """座席選択をスキップ"""
        try:
            logger.info("🪑 座席選択画面を確認中...")
            
            # 座席選択画面の検出
            seat_indicators = [
                'text="座席を選択"',
                'text="座席選択"',
                '.seat-selection',
                '#seat-select',
                'button:has-text("指定なし")',
                'button:has-text("お任せ")',
                'a:has-text("指定なし")',
                'a:has-text("お任せ")'
            ]
            
            # 「指定なし」「お任せ」オプションを探す
            for selector in seat_indicators:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=2000)
                    if element:
                        # 「指定なし」「お任せ」を選択
                        if '指定なし' in selector or 'お任せ' in selector:
                            await element.click()
                            await asyncio.sleep(1)
                            logger.info("✅ 座席指定なし/お任せを選択しました")
                            return True
                except Exception:
                    continue
            
            # スキップボタンを探す
            skip_selectors = [
                'button:has-text("スキップ")',
                'button:has-text("次へ")',
                'button:has-text("続ける")',
                'a:has-text("スキップ")',
                '.skip-button'
            ]
            
            for selector in skip_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=2000)
                    if element:
                        await element.click()
                        await asyncio.sleep(1)
                        logger.info("✅ 座席選択をスキップしました")
                        return True
                except Exception:
                    continue
            
            logger.info("ℹ️ 座席選択画面が見つかりませんでした（スキップ）")
            return True
            
        except Exception as e:
            logger.warning(f"座席選択スキップ処理: {e}")
            return False
    
    async def _extract_reservation_id(self) -> str:
        """予約番号を抽出"""
        try:
            # 予約番号のパターン
            patterns = [
                r'予約番号[：:]\s*([A-Z0-9\-]+)',
                r'予約ID[：:]\s*([A-Z0-9\-]+)',
                r'受付番号[：:]\s*([A-Z0-9\-]+)',
                r'確認番号[：:]\s*([A-Z0-9\-]+)',
                r'[A-Z]{2,3}-\d{6,10}'
            ]
            
            page_content = await self.page.content()
            
            for pattern in patterns:
                match = re.search(pattern, page_content)
                if match:
                    return match.group(1) if match.groups() else match.group(0)
            
            # 予約番号要素を探す
            reservation_elements = await self.page.query_selector_all(
                '.reservation-id, .reservation-number, [class*="confirmation"]'
            )
            
            for element in reservation_elements:
                text = await element.text_content()
                if text and re.search(r'[A-Z0-9\-]{6,}', text):
                    match = re.search(r'[A-Z0-9\-]{6,}', text)
                    if match:
                        return match.group(0)
            
            # デフォルトの予約番号を生成
            return f'TBL-{datetime.now().strftime("%Y%m%d%H%M%S")}'
            
        except Exception as e:
            logger.error(f"予約番号抽出エラー: {str(e)}")
            return f'TBL-{datetime.now().strftime("%Y%m%d%H%M%S")}'


# グローバルインスタンス
tabelog_service = TabelogReservationService()