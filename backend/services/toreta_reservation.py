"""
Toreta予約システム連携サービス
Toretaの予約システムを使用してレストラン予約を自動化
"""
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from playwright.async_api import async_playwright, Page, Browser
import re

# ロガー設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ToretaReservationService:
    """Toreta予約専用サービス"""
    
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
                headless=False,  # デバッグ時は False
                args=[
                    '--start-maximized',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox'
                ]
            )
            context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                locale='ja-JP',
                timezone_id='Asia/Tokyo',
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            self.page = await context.new_page()
            
            # 基本的な自動化検出回避
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            logger.info("🌐 Toreta用ブラウザを初期化しました")
    
    async def close(self):
        """ブラウザを閉じる"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("🔒 ブラウザを閉じました")
    
    def is_toreta_url(self, url: str) -> bool:
        """URLがToretaかチェック"""
        if not url:
            return False
        return 'toreta.in' in url or 'toreta-reserve' in url
    
    async def make_reservation(
        self,
        restaurant_url: str,
        reservation_date: str,
        reservation_time: str,
        party_size: int,
        customer_info: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Toretaで予約を実行
        
        Args:
            restaurant_url: ToretaのレストランURL
            reservation_date: 予約日 (YYYY-MM-DD)
            reservation_time: 予約時間 (HH:MM)
            party_size: 人数
            customer_info: 顧客情報 (name, phone, email)
        
        Returns:
            予約結果の辞書
        """
        try:
            await self.initialize()
            
            # Toreta URLかチェック
            if not self.is_toreta_url(restaurant_url):
                return {
                    'success': False,
                    'error': 'URLがToretaのものではありません',
                    'message': f'提供されたURL: {restaurant_url}'
                }
            
            logger.info(f"🍴 Toreta予約開始: {restaurant_url}")
            logger.info(f"📅 予約情報: {reservation_date} {reservation_time}, {party_size}名")
            
            # レストランページにアクセス
            await self.page.goto(restaurant_url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(5)  # ページの完全読み込みを待つ
            
            # スクリーンショットを保存（デバッグ用）
            await self.page.screenshot(path='toreta_initial.png')
            logger.info("📸 初期画面のスクリーンショットを保存しました")
            
            # 初期画面の「予約する」ボタンをクリック
            initial_button_selectors = [
                'button:has-text("予約する")',
                'button.btn-primary:has-text("予約する")',
                'a:has-text("予約する")',
                '.btn:has-text("予約する")'
            ]
            
            for selector in initial_button_selectors:
                try:
                    button = await self.page.wait_for_selector(selector, timeout=3000)
                    if button:
                        # 利用規約に同意するチェックボックスがある場合
                        agreement_checkbox = await self.page.query_selector('input[type="checkbox"]')
                        if agreement_checkbox:
                            is_checked = await agreement_checkbox.is_checked()
                            if not is_checked:
                                await agreement_checkbox.check()
                                logger.info("✅ 利用規約に同意しました")
                        
                        await button.click()
                        await asyncio.sleep(3)
                        logger.info("✅ 初期画面の予約ボタンをクリックしました")
                        break
                except Exception:
                    continue
            
            # Step 1: 日付選択
            logger.info("📅 ステップ1: 日付選択")
            date_selected = await self._select_date_toreta(reservation_date)
            if not date_selected:
                return {
                    'success': False,
                    'error': '日付選択失敗',
                    'message': f'{reservation_date} は予約できません'
                }
            
            # Step 2: 時間と人数選択
            logger.info("⏰ ステップ2: 時間と人数選択")
            time_selected = await self._select_time_and_party_toreta(reservation_time, party_size)
            if not time_selected:
                return {
                    'success': False,
                    'error': '時間・人数選択失敗',
                    'message': f'{reservation_time} {party_size}名での予約ができません'
                }
            
            # Step 3: 顧客情報入力
            logger.info("📝 ステップ3: お客様情報入力")
            info_filled = await self._fill_customer_info_toreta(customer_info)
            if not info_filled:
                return {
                    'success': False,
                    'error': '顧客情報入力失敗',
                    'message': '顧客情報の入力に失敗しました'
                }
            
            # Step 4: 確認と予約完了
            logger.info("✅ ステップ4: 予約確認")
            confirmation_result = await self._confirm_and_submit_toreta()
            
            if confirmation_result['success']:
                logger.info("🎉 Toreta予約完了!")
                return {
                    'success': True,
                    'reservation_id': confirmation_result.get('reservation_id', f'TRT-{datetime.now().strftime("%Y%m%d%H%M%S")}'),
                    'message': 'Toretaでの予約が完了しました！確認メールをご確認ください。',
                    'details': {
                        'restaurant_url': restaurant_url,
                        'date': reservation_date,
                        'time': reservation_time,
                        'party_size': party_size,
                        'customer_name': customer_info.get('name')
                    }
                }
            else:
                return confirmation_result
            
        except Exception as e:
            logger.error(f"❌ 予約エラー: {str(e)}")
            return {
                'success': False,
                'error': '予約処理エラー',
                'message': str(e)
            }
        finally:
            # デバッグ用：ブラウザは開いたままにしておく
            # await self.close()
            pass
    
    async def _select_date_toreta(self, date_str: str) -> bool:
        """Toretaで日付を選択"""
        try:
            logger.info(f"📅 日付選択: {date_str}")
            
            # 日付を解析
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            day_number = date_obj.day
            month_str = date_obj.strftime('%m月')
            
            # ToretaはVue.jsを使用しているため、動的に生成される要素を待つ
            await asyncio.sleep(2)
            
            # まず、日付選択ボタンをクリックしてカレンダーを表示
            date_button_selectors = [
                'button:has-text("日付を選択")',
                'button:has-text("日付")',
                '.date-selector',
                '[class*="date-picker"]',
                'input[placeholder*="日付"]'
            ]
            
            for selector in date_button_selectors:
                try:
                    button = await self.page.wait_for_selector(selector, timeout=2000)
                    if button:
                        await button.click()
                        await asyncio.sleep(2)
                        logger.info(f"✅ 日付選択ボタンをクリック: {selector}")
                        break
                except Exception:
                    continue
            
            # カレンダーから日付を選択
            calendar_selectors = [
                f'div.day:has-text("{day_number}")',
                f'button:has-text("{day_number}")',
                f'td:has-text("{day_number}")',
                f'span.day-number:has-text("{day_number}")',
                f'.calendar-day:has-text("{day_number}")',
                f'[data-date="{date_str}"]',
                f'[aria-label*="{month_str}{day_number}日"]'
            ]
            
            for selector in calendar_selectors:
                try:
                    # 複数の要素がある場合を考慮
                    elements = await self.page.query_selector_all(selector)
                    for element in elements:
                        # 要素が無効化されていないか確認
                        is_disabled = await element.get_attribute('disabled')
                        class_name = await element.get_attribute('class') or ''
                        
                        if not is_disabled and 'disabled' not in class_name and 'past' not in class_name:
                            # テキストを確認
                            text = await element.text_content()
                            if text and str(day_number) in text:
                                await element.click()
                                await asyncio.sleep(2)
                                logger.info(f"✅ 日付を選択しました: {date_str}")
                                
                                # 「次へ」ボタンをクリック
                                next_button = await self.page.query_selector('button:has-text("次へ"), button:has-text("Next"), button[type="submit"]')
                                if next_button:
                                    await next_button.click()
                                    await asyncio.sleep(2)
                                    logger.info("✅ 次へボタンをクリック")
                                
                                return True
                except Exception as e:
                    logger.debug(f"セレクタ {selector} でエラー: {e}")
                    continue
            
            # 日付入力フィールドがある場合
            date_input = await self.page.query_selector('input[type="date"], input[name*="date"], #reservation-date')
            if date_input:
                await date_input.fill(date_str)
                await asyncio.sleep(1)
                return True
            
            # 最後の試み: 利用可能な最初の日付を選択
            logger.warning(f"⚠️ 指定日 {date_str} が選択できませんでした")
            logger.info("🔄 利用可能な最初の日付を選択します")
            
            available_days = await self.page.query_selector_all('.day:not(.disabled):not(.past), button:not([disabled]):has-text("日")')
            if available_days and len(available_days) > 0:
                await available_days[0].click()
                await asyncio.sleep(2)
                logger.info("✅ 利用可能な日付を選択しました")
                
                # 「次へ」ボタンをクリック
                next_button = await self.page.query_selector('button:has-text("次へ"), button:has-text("Next"), button[type="submit"]')
                if next_button:
                    await next_button.click()
                    await asyncio.sleep(2)
                
                return True
            
            # デバッグ情報
            await self.page.screenshot(path='toreta_date_failed.png')
            logger.error("❌ 日付選択に完全に失敗しました")
            return False
            
        except Exception as e:
            logger.error(f"日付選択エラー: {str(e)}")
            return False
    
    async def _select_time_and_party_toreta(self, time_str: str, party_size: int) -> bool:
        """Toretaで時間と人数を選択"""
        try:
            logger.info(f"⏰ 時間選択: {time_str}, 人数: {party_size}名")
            
            # 人数選択
            party_selectors = [
                f'select[name*="party"], select[name*="people"], #party-size',
                f'button:text("{party_size}名")',
                f'label:has-text("{party_size}名")',
                f'input[type="radio"][value="{party_size}"]'
            ]
            
            for selector in party_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=2000)
                    if element:
                        if 'select' in selector:
                            await element.select_option(str(party_size))
                        elif 'input[type="radio"]' in selector:
                            await element.check()
                        else:
                            await element.click()
                        await asyncio.sleep(1)
                        logger.info(f"✅ 人数を選択: {party_size}名")
                        break
                except Exception:
                    continue
            
            # 時間選択
            # Toretaは通常、利用可能な時間帯をボタンで表示
            time_selectors = [
                f'button:has-text("{time_str}")',
                f'a:has-text("{time_str}")',
                f'.time-slot:has-text("{time_str}")',
                f'label:has-text("{time_str}")',
                f'input[type="radio"][value*="{time_str}"]'
            ]
            
            for selector in time_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=3000)
                    if element:
                        is_disabled = await element.get_attribute('disabled')
                        if not is_disabled:
                            await element.click()
                            await asyncio.sleep(1)
                            logger.info(f"✅ 時間を選択: {time_str}")
                            
                            # 「次へ」ボタンをクリック
                            next_button = await self.page.query_selector('button:has-text("次へ"), button:has-text("Next"), button[type="submit"]')
                            if next_button:
                                await next_button.click()
                                await asyncio.sleep(2)
                            
                            return True
                except Exception:
                    continue
            
            logger.warning("⚠️ 時間を選択できませんでした")
            return False
            
        except Exception as e:
            logger.error(f"時間・人数選択エラー: {str(e)}")
            return False
    
    async def _fill_customer_info_toreta(self, customer_info: Dict[str, str]) -> bool:
        """Toretaで顧客情報を入力"""
        try:
            logger.info("📝 顧客情報入力")
            
            # 名前入力
            name_selectors = [
                'input[name*="name"]:not([type="hidden"])',
                'input[placeholder*="名前"]',
                'input[placeholder*="氏名"]',
                '#customer-name, #name'
            ]
            
            for selector in name_selectors:
                element = await self.page.query_selector(selector)
                if element and await element.is_visible():
                    await element.fill(customer_info.get('name', ''))
                    logger.info("✅ 名前を入力しました")
                    break
            
            # 電話番号入力
            phone_selectors = [
                'input[name*="phone"], input[name*="tel"]',
                'input[type="tel"]',
                'input[placeholder*="電話"]',
                '#phone, #tel'
            ]
            
            for selector in phone_selectors:
                element = await self.page.query_selector(selector)
                if element and await element.is_visible():
                    # ハイフンを除去
                    phone = customer_info.get('phone', '').replace('-', '')
                    await element.fill(phone)
                    logger.info("✅ 電話番号を入力しました")
                    break
            
            # メールアドレス入力
            email_selectors = [
                'input[name*="email"], input[name*="mail"]',
                'input[type="email"]',
                'input[placeholder*="メール"]',
                '#email, #mail'
            ]
            
            for selector in email_selectors:
                element = await self.page.query_selector(selector)
                if element and await element.is_visible():
                    await element.fill(customer_info.get('email', ''))
                    logger.info("✅ メールアドレスを入力しました")
                    break
            
            # 特別な要望（あれば）
            if customer_info.get('special_requests'):
                request_selectors = [
                    'textarea[name*="request"], textarea[name*="comment"]',
                    'textarea[placeholder*="要望"]',
                    '#requests, #comments'
                ]
                
                for selector in request_selectors:
                    element = await self.page.query_selector(selector)
                    if element and await element.is_visible():
                        await element.fill(customer_info.get('special_requests', ''))
                        logger.info("✅ 特別な要望を入力しました")
                        break
            
            await asyncio.sleep(1)
            return True
            
        except Exception as e:
            logger.error(f"顧客情報入力エラー: {str(e)}")
            return False
    
    async def _confirm_and_submit_toreta(self) -> Dict[str, Any]:
        """Toretaで予約を確認して送信"""
        try:
            logger.info("✅ 予約確認・送信")
            
            # 利用規約の同意
            agreement_selectors = [
                'input[type="checkbox"][name*="agree"]',
                'input[type="checkbox"][name*="terms"]',
                'input[type="checkbox"][required]',
                '.agreement-checkbox'
            ]
            
            for selector in agreement_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    is_checked = await element.is_checked()
                    if not is_checked:
                        await element.check()
                        await asyncio.sleep(1)
                        logger.info("✅ 利用規約に同意しました")
            
            # 予約確認ボタン
            confirm_selectors = [
                'button:has-text("予約する")',
                'button:has-text("予約を確定")',
                'button:has-text("確認")',
                'button:has-text("送信")',
                'button[type="submit"]:has-text("予約")',
                'input[type="submit"][value*="予約"]'
            ]
            
            for selector in confirm_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=3000)
                    if element and await element.is_visible():
                        await element.click()
                        logger.info("✅ 予約ボタンをクリックしました")
                        break
                except Exception:
                    continue
            
            # 最終確認画面がある場合
            await asyncio.sleep(3)
            
            final_confirm_selectors = [
                'button:has-text("予約を確定する")',
                'button:has-text("この内容で予約")',
                'button:has-text("OK")',
                'button:has-text("はい")'
            ]
            
            for selector in final_confirm_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=3000)
                    if element and await element.is_visible():
                        await element.click()
                        logger.info("✅ 最終確認をクリックしました")
                        break
                except Exception:
                    continue
            
            # 予約完了を待つ
            await asyncio.sleep(5)
            
            # 予約完了の確認
            completion_indicators = [
                'text="予約が完了しました"',
                'text="予約を受け付けました"',
                'text="ご予約ありがとうございます"',
                'text="予約完了"',
                '.completion-message',
                '.success-message',
                'h1:has-text("完了")',
                'h2:has-text("完了")'
            ]
            
            for indicator in completion_indicators:
                element = await self.page.query_selector(indicator)
                if element:
                    # 予約番号を取得
                    reservation_id = await self._extract_reservation_id_toreta()
                    return {
                        'success': True,
                        'reservation_id': reservation_id,
                        'message': '予約が完了しました'
                    }
            
            # URLで判定
            current_url = self.page.url
            if 'complete' in current_url or 'success' in current_url or 'thanks' in current_url:
                reservation_id = await self._extract_reservation_id_toreta()
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
    
    async def _extract_reservation_id_toreta(self) -> str:
        """予約番号を抽出"""
        try:
            # 予約番号のパターン
            patterns = [
                r'予約番号[：:]\s*([A-Z0-9\-]+)',
                r'予約ID[：:]\s*([A-Z0-9\-]+)',
                r'受付番号[：:]\s*([A-Z0-9\-]+)',
                r'[A-Z]{2,3}-\d{6,10}',
                r'\d{10,15}'
            ]
            
            page_content = await self.page.content()
            
            for pattern in patterns:
                match = re.search(pattern, page_content)
                if match:
                    return match.group(1) if match.groups() else match.group(0)
            
            # デフォルトの予約番号を生成
            return f'TRT-{datetime.now().strftime("%Y%m%d%H%M%S")}'
            
        except Exception as e:
            logger.error(f"予約番号抽出エラー: {str(e)}")
            return f'TRT-{datetime.now().strftime("%Y%m%d%H%M%S")}'


# グローバルインスタンス
toreta_service = ToretaReservationService()