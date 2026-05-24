import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import {
  DEFAULT_LANG,
  LOCALE_MAP,
  PAGE_TITLES,
  translate,
} from './translations.js'

const STORAGE_KEY = 'aquamonitor-lang'

const LanguageContext = createContext(null)

function readStoredLang() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'en' || stored === 'ru') return stored
  } catch {
    /* ignore */
  }
  return DEFAULT_LANG
}

export function LanguageProvider({ children }) {
  const [lang, setLangState] = useState(readStoredLang)

  const setLang = useCallback((code) => {
    if (code !== 'en' && code !== 'ru') return
    setLangState(code)
    try {
      localStorage.setItem(STORAGE_KEY, code)
    } catch {
      /* ignore */
    }
  }, [])

  const t = useCallback((key, params) => translate(lang, key, params), [lang])

  const locale = LOCALE_MAP[lang] || LOCALE_MAP.en

  useEffect(() => {
    document.documentElement.lang = lang
    document.title = PAGE_TITLES[lang] || PAGE_TITLES.en
  }, [lang])

  const value = useMemo(() => ({ lang, setLang, t, locale }), [lang, setLang, t, locale])

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  const ctx = useContext(LanguageContext)
  if (!ctx) throw new Error('useLanguage must be used within LanguageProvider')
  return ctx
}
