import React, { useEffect, useRef, useState } from 'react'
import { api } from '../api.js'
import { useLanguage } from '../i18n/LanguageContext.jsx'

function renderMarkdownLight(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br/>')
    .replace(/_(.*?)_/g, '<em>$1</em>')
}

export function ChatPanel({ filters, open, onToggle }) {
  const { t, lang } = useLanguage()
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [suggestions, setSuggestions] = useState([])
  const bottomRef = useRef(null)

  useEffect(() => {
    if (open && messages.length === 0) {
      setMessages([{
        role: 'assistant',
        text: t('chat.welcome'),
        mode: 'rules',
      }])
      setSuggestions([
        t('chat.suggest1'),
        t('chat.suggest2'),
        t('chat.suggest3'),
      ])
    }
  }, [open, messages.length, t])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const send = async (text) => {
    const msg = (text || input).trim()
    if (!msg || loading) return
    setInput('')
    setMessages((m) => [...m, { role: 'user', text: msg }])
    setLoading(true)
    try {
      const res = await api.chat({ ...filters, message: msg, lang })
      setMessages((m) => [...m, { role: 'assistant', text: res.reply, mode: res.mode }])
      if (res.suggestions?.length) setSuggestions(res.suggestions)
    } catch (e) {
      setMessages((m) => [...m, { role: 'assistant', text: `${t('chat.error')} ${e.message}`, mode: 'error' }])
    } finally {
      setLoading(false)
    }
  }

  if (!open) {
    return (
      <button type="button" className="chat-fab" onClick={onToggle} aria-label={t('chat.open')}>
        <svg viewBox="0 0 24 24" width="22" height="22" fill="none" aria-hidden="true">
          <path d="M12 3a9 9 0 00-9 9c0 1.5.4 2.9 1 4.1L3 21l4.9-1.1A9 9 0 1012 3z" stroke="currentColor" strokeWidth="1.5"/>
        </svg>
      </button>
    )
  }

  return (
    <div className="chat-panel">
      <header className="chat-head">
        <div>
          <div className="chat-title">{t('chat.title')}</div>
          <div className="chat-sub">{t('chat.subtitle')}</div>
        </div>
        <button type="button" className="chat-close" onClick={onToggle} aria-label={t('chat.close')}>×</button>
      </header>

      <div className="chat-messages">
        {messages.map((m, i) => (
          <div key={i} className={`chat-bubble chat-bubble--${m.role}`}>
            {m.role === 'assistant' && m.mode && m.mode !== 'error' && (
              <span className="chat-mode">{m.mode === 'ollama' ? 'LLM' : t('chat.modeRules')}</span>
            )}
            <div
              dangerouslySetInnerHTML={{
                __html: m.role === 'assistant' ? renderMarkdownLight(m.text) : m.text,
              }}
            />
          </div>
        ))}
        {loading && (
          <div className="chat-bubble chat-bubble--assistant chat-bubble--typing">
            {t('chat.thinking')}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {suggestions.length > 0 && (
        <div className="chat-suggestions">
          {suggestions.slice(0, 3).map((s) => (
            <button key={s} type="button" className="chat-suggest-btn" onClick={() => send(s)}>
              {s}
            </button>
          ))}
        </div>
      )}

      <form
        className="chat-input-row"
        onSubmit={(e) => {
          e.preventDefault()
          send()
        }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={t('chat.placeholder')}
          maxLength={500}
        />
        <button type="submit" className="chat-send" disabled={loading || !input.trim()}>
          {t('chat.send')}
        </button>
      </form>
    </div>
  )
}
