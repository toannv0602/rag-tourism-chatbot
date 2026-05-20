export default function ConnectionStatus({ connected }) {
  return (
    <div className="flex items-center gap-1.5 text-xs text-teal-100">
      <span
        className={`w-2 h-2 rounded-full ${connected ? 'bg-green-400' : 'bg-red-400 animate-pulse'}`}
      />
      {connected ? 'Connected' : 'Reconnecting…'}
    </div>
  )
}
