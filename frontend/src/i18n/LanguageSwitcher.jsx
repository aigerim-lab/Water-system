import React from 'react'
import { LANGUAGES } from './translations.js'
import { useLanguage } from './LanguageContext.jsx'

export function LanguageSwitcher() {
  const { lang, setLang } = useLanguage()

  return (
    <div className="lang-switch" role="group" aria-label="Language">
      {LANGUAGES.map(({ code, label }) => (
        <button
          key={code}
          type="button"
          className={`lang-switch-btn ${lang === code ? 'active' : ''}`}
          onClick={() => setLang(code)}
          aria-pressed={lang === code}
        >
          {label}
        </button>
      ))}
    </div>
  )
}
