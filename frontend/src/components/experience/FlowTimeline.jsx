import React from 'react'
import { useLanguage } from '../../i18n/LanguageContext.jsx'

/** Year scrubber with data-driven flow — bar fill = progress through selected year range */
export function FlowTimeline({ yearMin, yearMax, yearFocus, onChange, narrative }) {
  const { t } = useLanguage()
  if (yearMin == null || yearMax == null || yearMin >= yearMax) return null

  const focus = yearFocus ?? yearMax
  const progress = ((focus - yearMin) / (yearMax - yearMin)) * 100

  return (
    <div className="flow-timeline">
      <div className="flow-timeline__header">
        <span className="flow-timeline__label">{t('yearScrubber.label')}</span>
        <strong className="flow-timeline__year">{focus}</strong>
      </div>
      <div className="flow-timeline__river" aria-hidden="true">
        <span className="flow-timeline__fill" style={{ width: `${progress}%` }} />
        <span className="flow-timeline__current" style={{ left: `${progress}%` }} />
      </div>
      <input
        className="flow-timeline__input"
        type="range"
        min={yearMin}
        max={yearMax}
        value={focus}
        onChange={(e) => onChange(Number(e.target.value))}
        aria-valuemin={yearMin}
        aria-valuemax={yearMax}
        aria-valuenow={focus}
      />
      <div className="flow-timeline__range">
        <span>{yearMin}</span>
        <span>{yearMax}</span>
      </div>
      {narrative && <p className="flow-timeline__narrative">{narrative}</p>}
    </div>
  )
}
