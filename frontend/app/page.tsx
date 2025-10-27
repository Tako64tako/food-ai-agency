'use client'

import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { ChevronRightIcon, StarIcon, MapPinIcon, ClockIcon, UserGroupIcon } from '@heroicons/react/24/solid'
import { MagnifyingGlassIcon, ChatBubbleLeftRightIcon, SparklesIcon } from '@heroicons/react/24/outline'

interface Restaurant {
  name: string
  score: number
  reason: string
  address: string
  rating: number
  place_id?: string
  types?: string[]
  photo_url?: string
  price_level?: number
  price_level_text?: string
  website?: string
  phone_number?: string
  opening_hours?: any
  url?: string
}

interface ReservationSession {
  session_id: string
  step: string
  message: string
  options?: string[]
  processing?: boolean
  error?: boolean
  success?: boolean
  cancelled?: boolean
  restart_needed?: boolean
}

interface SearchResult {
  message: string
  conditions: any
  restaurants: Restaurant[]
  has_more?: boolean
}

interface ChatMessage {
  type: 'user' | 'ai'
  content: string
  restaurants?: Restaurant[]
}

// 予約フォームコンポーネント
const ReservationForm = ({ onSubmit, sessionId, isLoading }: {
  onSubmit: (data: any) => void;
  sessionId: string;
  isLoading: boolean;
}) => {
  const [formData, setFormData] = useState({
    date: '',
    time: '',
    partySize: '',
    name: '',
    phone: '',
    email: '',
    specialRequests: ''
  });

  const [selectedTime, setSelectedTime] = useState('');

  const timeSlots = ['11:00', '11:30', '12:00', '12:30', '17:30', '18:00', '18:30', '19:00', '19:30', '20:00', '20:30', '21:00'];
  const partySizeOptions = ['1', '2', '3', '4', '5', '6', '7', '8'];

  const handleSubmit = () => {
    if (formData.date && formData.time && formData.partySize && formData.name && formData.phone && formData.email) {
      // メールアドレスの簡単な検証
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(formData.email)) {
        alert('正しいメールアドレスを入力してください。');
        return;
      }
      onSubmit(formData);
    } else {
      alert('必須項目をすべて入力してください。（日付、時間、人数、名前、電話番号、メールアドレス）');
    }
  };

  return (
    <div className="mb-6">
      <div className="bg-gray-50 p-6 rounded-lg">
        <h3 className="text-xl font-semibold text-gray-800 mb-6">📝 予約情報入力</h3>
        
        {/* 日付選択 */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">日付 *</label>
          <input
            type="date"
            value={formData.date}
            min={new Date().toISOString().split('T')[0]}
            max={new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]}
            onChange={(e) => setFormData(prev => ({ ...prev, date: e.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-800"
          />
        </div>

        {/* 時間選択 */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">時間 *</label>
          <div className="grid grid-cols-4 gap-2">
            {timeSlots.map((time) => (
              <button
                key={time}
                onClick={() => {
                  setFormData(prev => ({ ...prev, time }));
                  setSelectedTime(time);
                }}
                className={`p-2 border rounded-lg transition-colors text-sm ${
                  selectedTime === time 
                    ? 'bg-blue-500 text-white border-blue-500' 
                    : 'bg-white border-gray-300 text-gray-800 hover:bg-blue-50 hover:border-blue-300'
                }`}
              >
                {time}
              </button>
            ))}
          </div>
        </div>

        {/* 人数選択 */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">人数 *</label>
          <div className="grid grid-cols-4 gap-2">
            {partySizeOptions.map((size) => (
              <button
                key={size}
                onClick={() => setFormData(prev => ({ ...prev, partySize: size }))}
                className={`p-2 border rounded-lg transition-colors text-sm ${
                  formData.partySize === size 
                    ? 'bg-blue-500 text-white border-blue-500' 
                    : 'bg-white border-gray-300 text-gray-800 hover:bg-blue-50 hover:border-blue-300'
                }`}
              >
                {size}名
              </button>
            ))}
          </div>
        </div>

        {/* 連絡先情報 */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-3">連絡先情報 *</label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-2">お名前</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="田中太郎"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-800"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-2">電話番号</label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData(prev => ({ ...prev, phone: e.target.value }))}
                placeholder="090-1234-5678"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-800"
              />
            </div>
          </div>
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-600 mb-2">メールアドレス</label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
              placeholder="tanaka@example.com"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-800"
            />
            <p className="text-xs text-gray-500 mt-1">確認メールが送信されます</p>
          </div>
        </div>

        {/* 特別要望 */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">特別なご要望</label>
          <textarea
            value={formData.specialRequests}
            onChange={(e) => setFormData(prev => ({ ...prev, specialRequests: e.target.value }))}
            placeholder="誕生日のお祝い、アレルギー情報、席の希望など"
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-800"
          />
        </div>


        {/* フォーム送信ボタン */}
        <div className="mt-6">
          <button
            onClick={handleSubmit}
            disabled={isLoading}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                処理中...
              </div>
            ) : (
              '🎯 予約情報を送信'
            )}
          </button>
        </div>

        {/* 選択内容の確認 */}
        {(formData.date || formData.time || formData.partySize) && (
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800 font-medium">現在の選択内容:</p>
            <ul className="text-sm text-blue-700 mt-1">
              {formData.date && <li>📅 日付: {formData.date}</li>}
              {formData.time && <li>🕐 時間: {formData.time}</li>}
              {formData.partySize && <li>👥 人数: {formData.partySize}名</li>}
              {formData.name && <li>👤 お名前: {formData.name}</li>}
              {formData.phone && <li>📞 電話番号: {formData.phone}</li>}
              {formData.email && <li>📧 メール: {formData.email}</li>}
              {formData.specialRequests && <li>💭 要望: {formData.specialRequests}</li>}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default function Home() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [showResults, setShowResults] = useState(false)
  const [currentRestaurants, setCurrentRestaurants] = useState<Restaurant[]>([])
  const [selectedRestaurant, setSelectedRestaurant] = useState<Restaurant | null>(null)
  const [showModal, setShowModal] = useState(false)
  const [conversationHistory, setConversationHistory] = useState<string[]>([])
  const [lastSearchConditions, setLastSearchConditions] = useState<any>(null)
  const [hasMoreResults, setHasMoreResults] = useState(true)
  const [currentPage, setCurrentPage] = useState(1)
  const [showReservationModal, setShowReservationModal] = useState(false)
  const [currentReservationSession, setCurrentReservationSession] = useState<ReservationSession | null>(null)
  const [reservationInput, setReservationInput] = useState('')
  const [reservationLoading, setReservationLoading] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      type: 'ai',
      content: 'こんにちは！食事処提案AIです。どのようなお店をお探しですか？'
    }
  ])

  const handleSearch = async () => {
    if (!query.trim() || loading) return

    const userMessage: ChatMessage = { type: 'user', content: query }
    setMessages(prev => [...prev, userMessage])
    const currentQuery = query
    
    // 会話履歴を更新
    const newHistory = [...conversationHistory, currentQuery]
    setConversationHistory(newHistory)
    
    setQuery('')
    setLoading(true)
    setCurrentPage(1) // 新しい検索時はページをリセット
    setHasMoreResults(true)

    try {
      // 会話履歴と前回の検索条件を含めて送信
      const searchPayload = {
        query: currentQuery,
        conversation_history: newHistory,
        last_conditions: lastSearchConditions,
        page: 1
      }

      const response = await axios.post('/api/search', 
        searchPayload,
        {
          headers: {
            'Content-Type': 'application/json'
          },
          timeout: 30000 // 30秒タイムアウト
        }
      )
      
      const result: SearchResult = response.data

      const aiMessage: ChatMessage = {
        type: 'ai',
        content: result.message
      }

      setMessages(prev => [...prev, aiMessage])
      
      // 検索条件を保存
      if (result.conditions) {
        setLastSearchConditions(result.conditions)
      }
      
      // レストラン結果を分離表示
      if (result.restaurants && result.restaurants.length > 0) {
        setCurrentRestaurants(result.restaurants)
        setShowResults(true)
        setHasMoreResults(result.has_more || false)
      } else {
        setCurrentRestaurants([])
        setHasMoreResults(false)
      }
    } catch (error: any) {
      console.error('検索エラー:', error)
      
      let errorMessage = '申し訳ございません。検索中にエラーが発生しました。'
      
      if (error.response) {
        // サーバーからのエラーレスポンス
        const status = error.response.status
        const errorData = error.response.data
        
        console.log('Response status:', status)
        console.log('Response data:', errorData)
        
        if (status === 404) {
          errorMessage = 'APIエンドポイントが見つかりません。サーバーが正しく起動しているか確認してください。'
        } else if (status === 500) {
          errorMessage = 'サーバー内部エラーが発生しました。'
          if (errorData.error) {
            errorMessage += `\n詳細: ${errorData.error}`
          }
        } else if (errorData.error) {
          errorMessage = errorData.error
        } else if (errorData.message) {
          errorMessage = errorData.message
        }
      } else if (error.request) {
        // ネットワークエラー
        errorMessage = 'サーバーに接続できませんでした。\n• バックエンドサーバーが起動しているか確認してください (http://localhost:5000)\n• ネットワーク接続を確認してください'
      } else if (error.code === 'ECONNABORTED') {
        // タイムアウトエラー
        errorMessage = 'リクエストがタイムアウトしました。しばらくしてからもう一度お試しください。'
      }
      
      const errorMessageObj: ChatMessage = {
        type: 'ai',
        content: errorMessage
      }
      setMessages(prev => [...prev, errorMessageObj])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSearch()
    }
  }

  const handleShowDetails = (restaurant: Restaurant) => {
    setSelectedRestaurant(restaurant)
    setShowModal(true)
  }

  const handleCloseModal = () => {
    setShowModal(false)
    setSelectedRestaurant(null)
  }

  const handleShowMap = (restaurant: Restaurant) => {
    // Google Mapsで店舗を開く
    let mapsUrl
    if (restaurant.url) {
      // Google MapsページのURLがある場合はそれを使用
      mapsUrl = restaurant.url
    } else {
      // ない場合は検索クエリで開く
      const query = encodeURIComponent(restaurant.address || restaurant.name)
      mapsUrl = `https://www.google.com/maps/search/?api=1&query=${query}`
    }
    window.open(mapsUrl, '_blank')
  }

  const handleMakeReservation = async (restaurant: Restaurant) => {
    console.log('🤖 AI予約ボタンがクリックされました:', restaurant.name)
    
    try {
      setReservationLoading(true)
      console.log('📤 予約開始APIを呼び出し中...')
      
      const response = await axios.post('/api/reservation/start', {
        restaurant: restaurant,
        user_id: 'default'
      })
      
      console.log('📥 予約開始APIレスポンス:', response.data)
      
      // レスポンスデータの検証
      if (response.data && response.data.session_id) {
        console.log('✅ 予約セッション開始成功, session_id:', response.data.session_id)
        setCurrentReservationSession(response.data)
        setShowReservationModal(true)
        setShowModal(false) // 詳細モーダルを閉じる
      } else if (response.data && response.data.error && response.data.step === 'unavailable') {
        console.log('⚠️ 予約不可レストラン:', response.data.message)
        // 予約不可の場合も情報を表示
        setCurrentReservationSession(response.data)
        setShowReservationModal(true)
        setShowModal(false) // 詳細モーダルを閉じる
      } else {
        console.error('❌ セッションIDが見つかりません:', response.data)
        throw new Error('予約セッションの開始に失敗しました')
      }
      
    } catch (error: any) {
      console.error('❌ 予約開始エラー:', error)
      console.error('エラー詳細:', error.response?.data)
      alert(`予約システムの開始に失敗しました。\nエラー: ${error.response?.data?.error || error.message}\n直接お店にお電話ください。`)
    } finally {
      setReservationLoading(false)
      console.log('🔄 予約開始処理完了')
    }
  }

  const handleReservationStep = async () => {
    console.log('📤 予約ステップ送信開始')
    console.log('入力値:', reservationInput)
    console.log('現在のセッション:', currentReservationSession?.session_id)
    console.log('ローディング状態:', reservationLoading)
    
    if (!currentReservationSession || reservationLoading) {
      console.log('❌ 送信条件を満たしていません')
      return
    }

    if (!reservationInput.trim()) {
      console.log('⚠️ 入力値が空ですが、確認画面からの送信の可能性があります')
    }

    try {
      setReservationLoading(true)
      console.log('📤 予約ステップAPIを呼び出し中...')
      
      const response = await axios.post('/api/reservation/step', {
        session_id: currentReservationSession.session_id,
        user_input: reservationInput || '続行'  // 空の場合はデフォルト値
      })
      
      console.log('📥 予約ステップAPIレスポンス:', response.data)
      
      // エラーチェック
      if (response.data.error) {
        console.error('❌ APIからエラーレスポンス:', response.data)
        alert(`予約処理でエラーが発生しました。\n${response.data.error}`)
        
        if (response.data.restart_needed) {
          console.log('🔄 予約モーダルを閉じます（再起動が必要）')
          setShowReservationModal(false)
          setCurrentReservationSession(null)
        }
        return
      }
      
      // 正常なレスポンスの場合
      console.log('✅ 正常なレスポンスを受信:', response.data)
      console.log('📊 新しいステップ:', response.data.step)
      console.log('📝 メッセージ:', response.data.message)
      console.log('🎯 選択肢:', response.data.options)
      
      // 強制的に新しいオブジェクトとして更新
      setCurrentReservationSession(prev => ({
        ...response.data,
        timestamp: Date.now() // 強制再レンダリング用
      }))
      setReservationInput('')
      
      console.log('🔄 画面更新完了')
      
      // デバッグ: 状態更新後のログ (useEffect内で確認するため削除)
      
      // 予約完了またはキャンセルされた場合はモーダルを閉じる
      if (response.data.step === 'completed') {
        console.log('✅ 予約プロセス完了、3秒後にモーダルを閉じます')
        setTimeout(() => {
          setShowReservationModal(false)
          setCurrentReservationSession(null)
        }, 3000) // 3秒後に自動で閉じる
      }
      
    } catch (error: any) {
      console.error('❌ 予約ステップエラー:', error)
      console.error('エラー詳細:', error.response?.data)
      alert(`予約処理でエラーが発生しました。\nエラー: ${error.response?.data?.error || error.message}`)
    } finally {
      setReservationLoading(false)
      console.log('🔄 予約ステップ処理完了')
    }
  }

  const handleCloseReservationModal = () => {
    setShowReservationModal(false)
    setCurrentReservationSession(null)
    setReservationInput('')
  }

  const handleQuickReservationInput = (option: string) => {
    console.log('⚡ クイック選択ボタンがクリックされました:', option)
    setReservationInput(option)
    console.log('📝 入力フィールドに設定:', option)
  }

  // フォーム送信処理
  const handleFormSubmit = async (formData: any) => {
    console.log('📝 フォーム送信開始:', formData)
    setReservationLoading(true)

    try {
      const formattedData = `日時: ${formData.date} ${formData.time}, 人数: ${formData.partySize}名, 名前: ${formData.name}, 電話: ${formData.phone}, メール: ${formData.email}, 要望: ${formData.specialRequests || 'なし'}`
      console.log('📤 送信するデータ:', formattedData)
      
      const response = await axios.post('/api/reservation/step', {
        session_id: currentReservationSession?.session_id,
        user_input: formattedData
      })

      console.log('📥 フォーム送信APIレスポンス:', response.data)

      if (response.data.error) {
        console.error('❌ フォーム送信エラー:', response.data)
        alert(`予約処理でエラーが発生しました。\n${response.data.message}`)
        return
      }

      // 成功した場合は予約セッションを更新
      setCurrentReservationSession(prev => ({
        ...response.data,
        timestamp: Date.now()
      }))

      console.log('✅ フォーム送信成功')
    } catch (error) {
      console.error('❌ フォーム送信API呼び出しエラー:', error)
      alert('通信エラーが発生しました。もう一度お試しください。')
    } finally {
      setReservationLoading(false)
    }
  }

  // スコアに基づいてバッジのスタイルを決定
  const getScoreBadgeStyle = (score: number) => {
    if (score >= 90) return "bg-gradient-to-r from-emerald-500 to-green-600"
    if (score >= 80) return "bg-gradient-to-r from-blue-500 to-indigo-600"
    if (score >= 70) return "bg-gradient-to-r from-yellow-500 to-orange-600"
    return "bg-gradient-to-r from-gray-500 to-gray-600"
  }

  // スコアに基づいて説明テキストを決定
  const getScoreDescription = (score: number) => {
    if (score >= 90) return "非常におすすめ"
    if (score >= 80) return "おすすめ"
    if (score >= 70) return "まずまず"
    return "検討してみてください"
  }

  // もっと見る機能
  const handleLoadMore = async () => {
    if (loadingMore || !hasMoreResults || !lastSearchConditions) return

    setLoadingMore(true)
    const nextPage = currentPage + 1

    try {
      const searchPayload = {
        query: '', // 空にして、条件のみで検索
        conversation_history: conversationHistory,
        last_conditions: lastSearchConditions,
        page: nextPage
      }

      console.log('もっと見る - 送信データ:', searchPayload)

      const response = await axios.post('/api/search', 
        searchPayload,
        {
          headers: {
            'Content-Type': 'application/json'
          },
          timeout: 30000
        }
      )
      
      const result: SearchResult = response.data

      if (result.restaurants && result.restaurants.length > 0) {
        // 既存の結果に追加
        setCurrentRestaurants(prev => [...prev, ...result.restaurants])
        setCurrentPage(nextPage)
        setHasMoreResults(result.has_more || false)
      } else {
        setHasMoreResults(false)
      }

    } catch (error: any) {
      console.error('追加読み込みエラー:', error)
      console.error('エラー詳細:', error.response?.data)
      setHasMoreResults(false)
      
      // エラーメッセージを表示
      const errorMessage = error.response?.data?.error || '追加の検索結果の読み込みに失敗しました。'
      alert(errorMessage)
    } finally {
      setLoadingMore(false)
    }
  }

  // ESCキーでモーダルを閉じる
  useEffect(() => {
    const handleEscKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && showModal) {
        handleCloseModal()
      }
    }

    document.addEventListener('keydown', handleEscKey)
    return () => {
      document.removeEventListener('keydown', handleEscKey)
    }
  }, [showModal])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* ヘッダー */}
      <header className="bg-white/80 backdrop-blur-sm shadow-sm border-b border-gray-200">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full flex items-center justify-center">
                <SparklesIcon className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                  食事処提案AI
                </h1>
              </div>
            </div>
            <div className="hidden md:flex items-center space-x-4 text-sm text-gray-600">
              <div className="flex items-center space-x-1">
                <ChatBubbleLeftRightIcon className="w-4 h-4" />
                <span>チャット</span>
              </div>
              <div className="flex items-center space-x-1">
                <MagnifyingGlassIcon className="w-4 h-4" />
                <span>検索</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8">
        <div className="grid lg:grid-cols-2 gap-8 max-w-7xl mx-auto">{/* メインコンテンツエリア */}

          {/* チャット画面 */}
          <div className="bg-white rounded-2xl shadow-xl border border-gray-100">
            <div className="p-6 border-b border-gray-100">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-to-r from-green-400 to-blue-500 rounded-full flex items-center justify-center">
                  <ChatBubbleLeftRightIcon className="w-5 h-5 text-white" />
                </div>
                <h2 className="text-lg font-semibold text-gray-800">AIチャット</h2>
              </div>
            </div>
            
            {/* メッセージエリア */}
            <div className="h-96 overflow-y-auto p-6 space-y-4 bg-gray-50/50">
              {messages.map((message, index) => (
                <div key={index} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-xs lg:max-w-md px-4 py-3 rounded-xl shadow-sm ${
                    message.type === 'user' 
                      ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white' 
                      : 'bg-white text-gray-800 border border-gray-100'
                  }`}>
                    <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>
                  </div>
                </div>
              ))}
              
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-white text-gray-800 px-4 py-3 rounded-xl border border-gray-100 shadow-sm">
                    <div className="flex items-center space-x-3">
                      <div className="animate-spin rounded-full h-5 w-5 border-2 border-gray-300 border-t-blue-500"></div>
                      <span className="text-sm">AIが検索中...</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* 入力エリア */}
            <div className="border-t border-gray-100 p-6 bg-white">
              <div className="flex space-x-4">
                <div className="flex-1 relative">
                  <textarea
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="どのようなお店をお探しですか？（例：渋谷で静かな中華料理店）"
                    className="w-full p-4 pr-12 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-gray-800 placeholder-gray-400 bg-gray-50 transition-all"
                    rows={2}
                    disabled={loading}
                  />
                  <MagnifyingGlassIcon className="absolute right-4 top-4 w-5 h-5 text-gray-400" />
                </div>
                <button
                  onClick={handleSearch}
                  disabled={loading || !query.trim()}
                  className="px-8 py-4 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-xl hover:from-blue-600 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium shadow-lg hover:shadow-xl"
                >
                  {loading ? (
                    <div className="flex items-center space-x-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                      <span>検索中</span>
                    </div>
                  ) : (
                    <div className="flex items-center space-x-2">
                      <SparklesIcon className="w-4 h-4" />
                      <span>検索</span>
                    </div>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* 検索のヒント */}
          {!showResults && (
            <div className="mt-8 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-8 border border-blue-100">
              <div className="text-center mb-6">
                <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <SparklesIcon className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-gray-800 mb-2">AIに話しかけてみてください</h3>
                <p className="text-gray-600">自然な言葉で、どんなお店を探しているか教えてください</p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[
                  { icon: "🍜", text: "中華料理を食べたい", desc: "基本的な検索" },
                  { icon: "🍷", text: "渋谷で静かなお店で3人で飲みたい", desc: "詳細な条件" },
                  { icon: "💰", text: "ランチで1000円以下のイタリアン", desc: "予算指定" },
                  { icon: "💕", text: "デートにおすすめの落ち着いたフレンチ", desc: "雰囲気重視" }
                ].map((example, idx) => (
                  <div 
                    key={idx}
                    onClick={() => setQuery(example.text)}
                    className="bg-white p-4 rounded-xl border border-gray-100 hover:border-blue-200 cursor-pointer transition-all hover:shadow-md group"
                  >
                    <div className="flex items-start space-x-3">
                      <span className="text-2xl">{example.icon}</span>
                      <div className="flex-1">
                        <p className="font-medium text-gray-800 group-hover:text-blue-600 transition-colors">
                          "{example.text}"
                        </p>
                        <p className="text-sm text-gray-500 mt-1">{example.desc}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* レストラン表示エリア */}
          <div className="bg-white rounded-2xl shadow-xl border border-gray-100">
            <div className="p-6 border-b border-gray-100">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-gradient-to-r from-orange-400 to-red-500 rounded-full flex items-center justify-center">
                    <StarIcon className="w-5 h-5 text-white" />
                  </div>
                  <h2 className="text-lg font-semibold text-gray-800">おすすめのお店</h2>
                </div>
                {showResults && (
                  <button
                    onClick={() => setShowResults(false)}
                    className="text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    <span className="sr-only">閉じる</span>
                    ✕
                  </button>
                )}
              </div>
            </div>

            <div className="p-6">
              {!showResults ? (
                <div className="text-center py-12">
                  <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <MagnifyingGlassIcon className="w-10 h-10 text-gray-400" />
                  </div>
                  <h3 className="text-lg font-medium text-gray-600 mb-2">検索結果がここに表示されます</h3>
                  <p className="text-gray-400">左側のチャットでお店の条件を入力してください</p>
                </div>
              ) : (
                <div className="space-y-6">
                  {currentRestaurants.map((restaurant, idx) => (
                    <div key={idx} className="border border-gray-100 rounded-2xl overflow-hidden hover:shadow-lg transition-all group">
                      {/* レストラン写真 */}
                      {restaurant.photo_url && (
                        <div className="h-48 bg-gradient-to-r from-gray-100 to-gray-200 relative overflow-hidden">
                          <img 
                            src={restaurant.photo_url} 
                            alt={restaurant.name}
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                            onError={(e) => {
                              e.currentTarget.style.display = 'none';
                            }}
                          />
                          <div className="absolute top-4 left-4">
                            <span className="w-8 h-8 bg-white/90 backdrop-blur-sm text-gray-800 rounded-full flex items-center justify-center text-sm font-bold shadow-lg">
                              {idx + 1}
                            </span>
                          </div>
                        </div>
                      )}
                      
                      <div className="p-6">
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex-1">
                            <div className="flex items-center space-x-3 mb-2">
                              {!restaurant.photo_url && (
                                <span className="w-8 h-8 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                                  {idx + 1}
                                </span>
                              )}
                              <h3 className="text-xl font-bold text-gray-800 group-hover:text-blue-600 transition-colors">
                                {restaurant.name}
                              </h3>
                            </div>
                            <div className="flex items-center space-x-4 text-sm text-gray-600 mb-3">
                              <div className="flex items-center space-x-1">
                                <MapPinIcon className="w-4 h-4 text-gray-400" />
                                <span>{restaurant.address}</span>
                              </div>
                              {restaurant.rating > 0 && (
                                <div className="flex items-center space-x-1">
                                  <StarIcon className="w-4 h-4 text-yellow-400" />
                                  <span className="font-medium">{restaurant.rating}</span>
                                </div>
                              )}
                              {restaurant.price_level_text && restaurant.price_level_text !== "価格情報なし" && (
                                <div className="flex items-center space-x-1">
                                  <span className="text-green-600 font-medium">💰</span>
                                  <span className="font-medium text-green-700">{restaurant.price_level_text}</span>
                                </div>
                              )}
                            </div>
                          </div>
                          <div className="flex flex-col items-end space-y-2">
                            <div className={`${getScoreBadgeStyle(restaurant.score)} text-white px-4 py-2 rounded-full text-sm font-bold shadow-sm`}>
                              ✨ おすすめ度 {restaurant.score}
                            </div>
                            <span className="text-xs text-gray-500 text-right">{getScoreDescription(restaurant.score)}</span>
                          </div>
                        </div>

                        <div className="bg-gray-50 rounded-xl p-4 mb-4">
                          <h4 className="font-medium text-gray-800 mb-2">🤖 AIが選んだ理由</h4>
                          <p className="text-gray-700 text-sm leading-relaxed">{restaurant.reason}</p>
                        </div>

                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-4">
                            {restaurant.types && restaurant.types.length > 0 && (
                              <div className="flex flex-wrap gap-2">
                                {restaurant.types.slice(0, 3).map((type, typeIdx) => (
                                  <span key={typeIdx} className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-xs font-medium">
                                    {type}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                          <button 
                            onClick={() => handleShowDetails(restaurant)}
                            className="bg-gradient-to-r from-blue-500 to-indigo-600 text-white px-6 py-2 rounded-xl hover:from-blue-600 hover:to-indigo-700 transition-all font-medium shadow-md hover:shadow-lg"
                          >
                            <div className="flex items-center space-x-2">
                              <MapPinIcon className="w-4 h-4" />
                              <span>詳細を見る</span>
                            </div>
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                  
                  {/* もっと見るボタン */}
                  {hasMoreResults && (
                    <div className="flex justify-center mt-8">
                      <button
                        onClick={handleLoadMore}
                        disabled={loadingMore}
                        className="bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white px-8 py-3 rounded-xl font-medium shadow-lg hover:shadow-xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                      >
                        {loadingMore ? (
                          <>
                            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                            <span>読み込み中...</span>
                          </>
                        ) : (
                          <>
                            <span>もっと見る</span>
                            <ChevronRightIcon className="w-5 h-5" />
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

        </div>
      </div>

      {/* 詳細モーダル */}
      {showModal && selectedRestaurant && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={handleCloseModal}
        >
          <div 
            className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* モーダルヘッダー */}
            <div className="sticky top-0 bg-white border-b border-gray-100 p-6 rounded-t-2xl">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-gray-800">店舗詳細</h2>
                <button
                  onClick={handleCloseModal}
                  className="w-8 h-8 bg-gray-100 hover:bg-gray-200 rounded-full flex items-center justify-center transition-colors"
                >
                  <span className="text-gray-600 text-xl">×</span>
                </button>
              </div>
            </div>

            {/* モーダルコンテンツ */}
            <div className="p-6">
              {/* 店舗画像 */}
              {selectedRestaurant.photo_url && (
                <div className="mb-6">
                  <img 
                    src={selectedRestaurant.photo_url} 
                    alt={selectedRestaurant.name}
                    className="w-full h-64 object-cover rounded-xl shadow-lg"
                    onError={(e) => {
                      e.currentTarget.style.display = 'none';
                    }}
                  />
                </div>
              )}

              {/* 店舗基本情報 */}
              <div className="mb-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-3xl font-bold text-gray-800">{selectedRestaurant.name}</h3>
                  <div className="flex flex-col items-end space-y-1">
                    <div className={`${getScoreBadgeStyle(selectedRestaurant.score)} text-white px-4 py-2 rounded-full text-lg font-bold shadow-sm`}>
                      ✨ おすすめ度 {selectedRestaurant.score}
                    </div>
                    <span className="text-xs text-gray-500">{getScoreDescription(selectedRestaurant.score)} (100点満点)</span>
                  </div>
                </div>

                {/* 評価とアドレス */}
                <div className="space-y-3 mb-6">
                  <div className="flex items-center space-x-6">
                    {selectedRestaurant.rating > 0 && (
                      <div className="flex items-center space-x-2">
                        <StarIcon className="w-5 h-5 text-yellow-400" />
                        <span className="font-medium text-lg text-gray-800">{selectedRestaurant.rating}</span>
                        <span className="text-gray-600">/ 5.0</span>
                      </div>
                    )}
                    
                    {selectedRestaurant.price_level_text && selectedRestaurant.price_level_text !== "価格情報なし" && (
                      <div className="flex items-center space-x-2">
                        <span className="text-green-600 text-xl">💰</span>
                        <span className="font-medium text-lg text-green-700">{selectedRestaurant.price_level_text}</span>
                      </div>
                    )}
                  </div>
                  
                  <div className="flex items-start space-x-2">
                    <MapPinIcon className="w-5 h-5 text-gray-400 mt-1" />
                    <span className="text-gray-700">{selectedRestaurant.address}</span>
                  </div>

                  {selectedRestaurant.phone_number && (
                    <div className="flex items-center space-x-2">
                      <span className="w-5 h-5 text-gray-400">📞</span>
                      <a href={`tel:${selectedRestaurant.phone_number}`} className="text-blue-600 hover:text-blue-800 transition-colors">
                        {selectedRestaurant.phone_number}
                      </a>
                    </div>
                  )}

                  {selectedRestaurant.website && (
                    <div className="flex items-center space-x-2">
                      <span className="w-5 h-5 text-gray-400">🌐</span>
                      <a 
                        href={selectedRestaurant.website} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 transition-colors underline"
                      >
                        公式サイトを見る
                      </a>
                    </div>
                  )}
                </div>

                {/* カテゴリータグ */}
                {selectedRestaurant.types && selectedRestaurant.types.length > 0 && (
                  <div className="mb-6">
                    <h4 className="font-semibold text-gray-800 mb-3">カテゴリー</h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedRestaurant.types.map((type, idx) => (
                        <span key={idx} className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm font-medium">
                          {type}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* 推薦理由 */}
                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-100">
                  <h4 className="font-semibold text-gray-800 mb-3 flex items-center">
                    <SparklesIcon className="w-5 h-5 mr-2 text-blue-600" />
                    🤖 AIがこのお店を選んだ理由
                  </h4>
                  <p className="text-gray-700 leading-relaxed">{selectedRestaurant.reason}</p>
                </div>
              </div>

              {/* アクションボタン */}
              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-100">
                <button 
                  onClick={() => handleShowMap(selectedRestaurant)}
                  className="bg-gradient-to-r from-green-500 to-emerald-600 text-white py-3 px-6 rounded-xl hover:from-green-600 hover:to-emerald-700 transition-all font-medium shadow-lg hover:shadow-xl"
                >
                  <div className="flex items-center justify-center space-x-2">
                    <MapPinIcon className="w-5 h-5" />
                    <span>地図で見る</span>
                  </div>
                </button>
                
                <button 
                  onClick={() => {
                    console.log('🔥 AI予約ボタンクリック！')
                    console.log('レストランデータ:', selectedRestaurant)
                    console.log('ローディング状態:', reservationLoading)
                    handleMakeReservation(selectedRestaurant)
                  }}
                  disabled={reservationLoading}
                  className="bg-gradient-to-r from-blue-500 to-indigo-600 text-white py-3 px-6 rounded-xl hover:from-blue-600 hover:to-indigo-700 transition-all font-medium shadow-lg hover:shadow-xl disabled:opacity-50"
                >
                  <div className="flex items-center justify-center space-x-2">
                    {reservationLoading ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        <span>開始中...</span>
                      </>
                    ) : (
                      <>
                        <span>🤖</span>
                        <span>AI予約</span>
                      </>
                    )}
                  </div>
                </button>

                {selectedRestaurant.website && (
                  <button 
                    onClick={() => window.open(selectedRestaurant.website, '_blank')}
                    className="col-span-2 bg-gradient-to-r from-purple-500 to-pink-600 text-white py-3 px-6 rounded-xl hover:from-purple-600 hover:to-pink-700 transition-all font-medium shadow-lg hover:shadow-xl"
                  >
                    <div className="flex items-center justify-center space-x-2">
                      <span>🌐</span>
                      <span>公式サイトを見る</span>
                    </div>
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 予約モーダル */}
      {showReservationModal && currentReservationSession && currentReservationSession.session_id && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden shadow-2xl">
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 className="text-2xl font-bold text-gray-800 flex items-center">
                <span className="mr-2">🤖</span>
                AI予約アシスタント
              </h2>
              <button 
                onClick={handleCloseReservationModal}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="p-6 max-h-[60vh] overflow-y-auto">
              {/* メッセージ表示 */}
              <div className="mb-6">
                <div className={`p-4 rounded-xl ${
                  currentReservationSession.error ? 'bg-red-50 border border-red-200' :
                  currentReservationSession.success ? 'bg-green-50 border border-green-200' :
                  'bg-blue-50 border border-blue-200'
                }`}>
                  <p className="whitespace-pre-line text-gray-800 leading-relaxed">
                    {currentReservationSession.message}
                  </p>
                </div>
                
              </div>

              {/* 予約フォームUI */}
              {currentReservationSession.step === 'datetime_input' ? (
                <ReservationForm 
                  onSubmit={handleFormSubmit}
                  sessionId={currentReservationSession.session_id}
                  isLoading={reservationLoading}
                />
              ) : (
                /* 他のステップのクイック選択オプション */
                currentReservationSession.options && (
                  <div className="mb-4">
                    <p className="text-sm text-gray-600 mb-3">選択してください:</p>
                    <div className="grid grid-cols-1 gap-3">
                      {currentReservationSession.options.map((option, index) => (
                        <button
                          key={index}
                          disabled={reservationLoading}
                          onClick={async () => {
                            console.log('🎯 確認画面ボタンクリック:', option)
                            console.log('📋 現在のセッション状態:', currentReservationSession?.step)
                            
                            // 予約実行ボタンの場合はローディング状態を表示
                            if (option.includes('✅')) {
                              setReservationLoading(true)
                              console.log('🔄 予約実行開始 - ローディング状態をONに')
                            }
                            
                            // 直接APIを呼び出し（reservationInputの状態更新を待たない）
                            console.log('📤 確認画面から直接API呼び出し:', option)
                            
                            try {
                              const response = await axios.post('/api/reservation/step', {
                                session_id: currentReservationSession?.session_id,
                                user_input: option
                              })
                              
                              console.log('📥 確認画面APIレスポンス:', response.data)
                              
                              if (response.data.error) {
                                console.error('❌ 確認画面エラー:', response.data)
                                alert(`予約処理でエラーが発生しました。\n${response.data.message}`)
                                return
                              }
                              
                              // 状態更新
                              setCurrentReservationSession(prev => ({
                                ...response.data,
                                timestamp: Date.now()
                              }))
                              
                              console.log('✅ 確認画面処理成功')
                            } catch (error) {
                              console.error('❌ 確認画面API呼び出しエラー:', error)
                              alert('通信エラーが発生しました。もう一度お試しください。')
                            } finally {
                              setReservationLoading(false)
                            }
                            
                            console.log('✅ ボタンクリック処理完了')
                          }}
                          className={`text-left p-4 rounded-lg transition-colors border-2 text-gray-800 font-medium ${
                            reservationLoading 
                              ? 'bg-gray-200 border-gray-300 cursor-not-allowed opacity-50'
                              : option.includes('✅') 
                              ? 'bg-green-50 border-green-300 hover:bg-green-100' 
                              : option.includes('📝')
                              ? 'bg-blue-50 border-blue-300 hover:bg-blue-100'
                              : 'bg-red-50 border-red-300 hover:bg-red-100'
                          }`}
                        >
                          {reservationLoading && option.includes('✅') ? (
                            <div className="flex items-center">
                              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-green-600 mr-2"></div>
                              処理中...
                            </div>
                          ) : (
                            option
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                )
              )}


              {/* 処理中表示 */}
              {currentReservationSession.processing && (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                  <p className="text-gray-600">AIが予約を処理しています...</p>
                </div>
              )}
            </div>

            {/* フッター */}
            <div className="p-4 border-t border-gray-200 bg-gray-50">
              <div className="flex justify-between items-center">
                <p className="text-xs text-gray-500">
                  セッションID: {currentReservationSession.session_id?.slice(-8) || 'N/A'}
                </p>
                <button
                  onClick={handleCloseReservationModal}
                  className="text-gray-600 hover:text-gray-800 transition-colors text-sm"
                >
                  閉じる
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
