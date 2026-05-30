import React, { useState } from 'react'
import { useLanguage } from '../../i18n/LanguageContext.jsx'
import { useSectionReveal } from '../../hooks/useSectionReveal.js'

const LEVELS = ['excellent', 'good', 'moderate', 'poor', 'dangerous']

export function WqiEducation({ embedded = false }) {
  const { t } = useLanguage()
  const { ref, className } = useSectionReveal()
  const [active, setActive] = useState('good')

  const inner = (
      <div className="wqi-edu" style={embedded ? { background: 'transparent', padding: 0 } : undefined}>
        <div className="wqi-edu__scale">
          {LEVELS.map((key) => (
            <button
              key={key}
              type="button"
              className={`wqi-edu__step wqi-edu__step--${key} ${active === key ? 'active' : ''}`}
              onClick={() => setActive(key)}
            >
              <span className="wqi-edu__range">{t(`wqi.${key}Range`)}</span>
              <span>{t(`wqi.${key}`)}</span>
            </button>
          ))}
        </div>
        <div className={`wqi-edu__detail wqi-edu__detail--${active}`}>
          <h3>{t(`wqi.${active}`)}</h3>
          <p>{t(`wqi.edu.${active}`)}</p>
        </div>
      </div>
  )

  if (embedded) return inner

  return (
    <section id="wqi" ref={ref} className={className}>
      <p className="section__eyebrow">{t('wqi.eduEyebrow')}</p>
      <h2 className="section__title">{t('wqi.title')}</h2>
      <p className="section__lead">{t('wqi.desc')}</p>
      {inner}
    </section>
  )
}
