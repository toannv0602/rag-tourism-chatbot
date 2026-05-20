import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

function TypingDots() {
  return (
    <span className="flex gap-1 items-center h-5 px-1">
      {[0, 150, 300].map((delay) => (
        <span
          key={delay}
          className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
          style={{ animationDelay: `${delay}ms` }}
        />
      ))}
    </span>
  )
}

// Custom renderers applied to every bot message
const markdownComponents = {
  p: ({ children }) => (
    <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>
  ),
  strong: ({ children }) => (
    <strong className="font-semibold text-gray-900">{children}</strong>
  ),
  a: ({ href, children }) => (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="text-teal-600 hover:text-teal-700 font-semibold underline underline-offset-2 transition-colors"
    >
      {children}
    </a>
  ),
  ol: ({ children }) => (
    <ol className="list-decimal list-outside ml-5 space-y-3 mt-2 mb-2">{children}</ol>
  ),
  ul: ({ children }) => (
    <ul className="list-disc list-outside ml-5 space-y-1 mt-2 mb-2">{children}</ul>
  ),
  li: ({ children }) => (
    <li className="leading-relaxed">{children}</li>
  ),
  code: ({ children }) => (
    <code className="bg-gray-100 text-teal-700 rounded px-1 py-0.5 text-xs font-mono">{children}</code>
  ),
  blockquote: ({ children }) => (
    <blockquote className="border-l-4 border-teal-300 pl-3 italic text-gray-500 my-2">{children}</blockquote>
  ),
}

export default function Message({ message }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex items-end gap-2 ${isUser ? 'flex-row-reverse' : ''}`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-teal-500 to-cyan-500 flex items-center justify-center text-white text-sm flex-shrink-0 shadow-sm">
          ✈
        </div>
      )}

      <div
        className={`max-w-[78%] rounded-2xl px-4 py-3 text-sm shadow-sm ${
          isUser
            ? 'bg-teal-600 text-white rounded-br-sm leading-relaxed'
            : message.error
              ? 'bg-red-50 text-red-700 border border-red-200 rounded-bl-sm'
              : 'bg-white text-gray-700 border border-gray-100 rounded-bl-sm'
        }`}
      >
        {/* Waiting for first token */}
        {message.streaming && !message.content && <TypingDots />}

        {/* User messages: plain text */}
        {isUser && message.content && (
          <span className="whitespace-pre-wrap">{message.content}</span>
        )}

        {/* Bot messages: always ReactMarkdown so formatting works even if done event is delayed.
            Append ▋ cursor during streaming so the caret appears inside the rendered markdown. */}
        {!isUser && message.content && (
          <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
            {message.streaming ? message.content + ' ▋' : message.content}
          </ReactMarkdown>
        )}
      </div>
    </div>
  )
}
