import { useState, useRef, useEffect, useCallback } from 'react'
import ChatWindow from './components/ChatWindow'
import InputBar from './components/InputBar'
import ConnectionStatus from './components/ConnectionStatus'

const WS_URL = 'ws://localhost:8000/api/ws/chat'

// Replace **Tour Name** with [**Tour Name**](url) for each known source
function embedTourLinks(text, sources) {
  let result = text
  for (const { name, url } of sources) {
    if (!url || !name) continue
    const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    result = result.replace(
      new RegExp(`\\*\\*(${escaped})\\*\\*`, 'g'),
      `[**$1**](${url})`,
    )
  }
  return result
}

const WELCOME_MESSAGE = {
  id: 'welcome',
  role: 'bot',
  content:
    "Hi there! I'm your Intrepid Travel consultant. Ask me about Asia tours, itineraries, prices, or what to expect on any adventure!",
  streaming: false,
}

export default function App() {
  const [messages, setMessages] = useState([WELCOME_MESSAGE])
  const [isStreaming, setIsStreaming] = useState(false)
  const [connected, setConnected] = useState(false)

  const wsRef = useRef(null)
  const botMsgIdRef = useRef(null)
  const reconnectTimerRef = useRef(null)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const ws = new WebSocket(WS_URL)

    ws.onopen = () => {
      setConnected(true)
      clearTimeout(reconnectTimerRef.current)
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)

      if (data.type === 'token') {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === botMsgIdRef.current
              ? { ...msg, content: msg.content + data.content }
              : msg,
          ),
        )
      } else if (data.type === 'done') {
        const sources = data.sources || []
        setMessages((prev) =>
          prev.map((msg) => {
            if (msg.id !== botMsgIdRef.current) return msg
            return {
              ...msg,
              content: embedTourLinks(msg.content, sources),
              streaming: false,
              sources,
            }
          }),
        )
        setIsStreaming(false)
        botMsgIdRef.current = null
      } else if (data.type === 'error') {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === botMsgIdRef.current
              ? { ...msg, content: data.content, streaming: false, error: true }
              : msg,
          ),
        )
        setIsStreaming(false)
        botMsgIdRef.current = null
      }
    }

    ws.onclose = () => {
      setConnected(false)
      // Clean up any in-progress stream so the UI doesn't get stuck
      if (botMsgIdRef.current) {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === botMsgIdRef.current ? { ...msg, streaming: false } : msg,
          ),
        )
        setIsStreaming(false)
        botMsgIdRef.current = null
      }
      reconnectTimerRef.current = setTimeout(connect, 2000)
    }

    ws.onerror = () => {
      ws.close()
    }

    wsRef.current = ws
  }, [])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectTimerRef.current)
      if (wsRef.current) {
        wsRef.current.onclose = null // prevent reconnect loop on unmount
        wsRef.current.close()
      }
    }
  }, [connect])

  const sendMessage = useCallback(
    (text) => {
      if (!text.trim() || isStreaming) return
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return

      const userMsgId = `user-${Date.now()}`
      const botMsgId = `bot-${Date.now()}`
      botMsgIdRef.current = botMsgId

      setMessages((prev) => [
        ...prev,
        { id: userMsgId, role: 'user', content: text, streaming: false },
        { id: botMsgId, role: 'bot', content: '', streaming: true },
      ])
      setIsStreaming(true)

      wsRef.current.send(JSON.stringify({ message: text }))
    },
    [isStreaming],
  )

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <header className="bg-gradient-to-r from-teal-600 to-cyan-600 text-white shadow-md flex-shrink-0">
        <div className="max-w-3xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-3xl">✈️</span>
            <div>
              <h1 className="text-lg font-bold leading-tight">Intrepid Travel Assistant</h1>
              <p className="text-xs text-teal-100">AI-powered tour consultant</p>
            </div>
          </div>
          <ConnectionStatus connected={connected} />
        </div>
      </header>

      <ChatWindow messages={messages} />

      <InputBar onSend={sendMessage} disabled={isStreaming || !connected} />
    </div>
  )
}
