import React, { useEffect, useState } from 'react'
import { useLanguage } from '../../i18n/LanguageContext.jsx'

const CHAPTERS = [
  { id: 'journey-overview', key: 'overview' },
  { id: 'journey-basins', key: 'basins' },
  { id: 'journey-lakes', key: 'lakes' },
  { id: 'journey-network', key: 'network' },
  { id: 'journey-pollution', key: 'pollution' },
  { id: 'journey-time', key: 'time' },
  { id: 'journey-regions', key: 'regions' },
  { id: 'journey-compare', key: 'compare' },
  { id: 'journey-forecast', key: 'forecast' },
]

export function JourneyNav({ visibleIds }) {
  const { t } = useLanguage()
  const [active, setActive] = useState('journey-overview')
  const ids = CHAPTERS.filter((c) => !visibleIds || visibleIds.has(c.id)).map((c) => c.id)

  useEffect(() => {
    const obs = new IntersectionObserver(
      (entries) => {
        const visible = entries.filter((e) => e.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)
        if (visible[0]?.target?.id) setActive(visible[0].target.id)
      },
      { rootMargin: '-20% 0px -55% 0px', threshold: [0, 0.25, 0.5] }
    )
    ids.forEach((id) => {
      const el = document.getElementById(id)
      if (el) obs.observe(el)
    })
    return () => obs.disconnect()
  }, [ids.join('|')])

  if (!ids.length) return null

  return (
    <nav className="journey-nav" aria-label={t('journey.navLabel')}>
      <span className="journey-nav__title">{t('journey.navTitle')}</span>
      <ol className="journey-nav__list">
        {CHAPTERS.filter((c) => ids.includes(c.id)).map((c, i) => (
          <li key={c.id}>
            <a
              href={`#${c.id}`}
              className={`journey-nav__link ${active === c.id ? 'journey-nav__link--on' : ''}`}
            >
              <span className="journey-nav__num">{String(i + 1).padStart(2, '0')}</span>
              {t(`journey.chapters.${c.key}`)}
            </a>
          </li>
        ))}
      </ol>
    </nav>
  )
}
