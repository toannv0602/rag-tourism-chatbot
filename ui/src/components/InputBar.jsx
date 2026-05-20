import { useState, useRef } from 'react'

const SUGGESTIONS = [
  'What tours do you have in Vietnam?',
  'How much does the Vietnam Express tour cost?',
  'What happens on day 3 of the tour?',
]

export default function InputBar({ onSend, disabled }) {
  const [text, setText] = useState('')
  const inputRef = useRef(null)

  const handleSubmit = (e) => {
    e.preventDefault()
    const trimmed = text.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setText('')
    inputRef.current?.focus()
  }

  const handleSuggestion = (suggestion) => {
    if (disabled) return
    onSend(suggestion)
    inputRef.current?.focus()
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <footer className="border-t border-gray-200 bg-white flex-shrink-0">
      {/* Quick suggestions — only shown when input is empty and not streaming */}
      {!text && !disabled && (
        <div className="max-w-3xl mx-auto px-4 pt-3 flex gap-2 flex-wrap">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => handleSuggestion(s)}
              className="text-xs text-teal-700 bg-teal-50 border border-teal-200 rounded-full px-3 py-1 hover:bg-teal-100 transition-colors"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit} className="max-w-3xl mx-auto px-4 py-3 flex gap-3">
        <textarea
          ref={inputRef}
          rows={1}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={disabled ? 'Waiting for response…' : 'Ask about tours, prices, itineraries…'}
          disabled={disabled}
          className="flex-1 resize-none rounded-xl border border-gray-300 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-400 leading-relaxed"
        />
        <button
          type="submit"
          disabled={disabled || !text.trim()}
          className="bg-teal-600 text-white px-5 rounded-xl font-medium text-sm hover:bg-teal-700 active:bg-teal-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center gap-1.5"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
            <path d="M3.105 2.288a.75.75 0 0 0-.826.95l1.414 4.926A1.5 1.5 0 0 0 5.135 9.25h6.115a.75.75 0 0 1 0 1.5H5.135a1.5 1.5 0 0 0-1.442 1.086l-1.414 4.926a.75.75 0 0 0 .826.95 28.897 28.897 0 0 0 15.293-7.155.75.75 0 0 0 0-1.114A28.897 28.897 0 0 0 3.105 2.288Z" />
          </svg>
          Send
        </button>
      </form>

      <p className="text-center text-xs text-gray-400 pb-3">
        Data from Travel
      </p>
    </footer>
  )
}
