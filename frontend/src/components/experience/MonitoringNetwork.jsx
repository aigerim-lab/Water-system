import React from 'react'
import { useLanguage } from '../../i18n/LanguageContext.jsx'

const STATUS_LABEL = {
  normal: 'gis.statusNormal',
  moderate: 'gis.statusModerate',
  high: 'gis.statusHigh',
}

export function MonitoringNetwork({ stations = [], onSelect, activeCode }) {
  const { t } = useLanguage()
  if (!stations.length) return null

  return (
    <div className="monitor-network">
      <div className="monitor-network__pulse" aria-hidden="true">
        {stations.map((s) => (
          <span
            key={s.code}
            className={`monitor-network__dot monitor-network__dot--${s.status}`}
            style={{ left: `${((s.lon - 46) / 40) * 100}%`, top: `${((55 - s.lat) / 18) * 100}%` }}
          />
        ))}
      </div>
      <div className="story-grid story-grid--stations">
        {stations.map((s) => (
          <button
            key={s.code}
            type="button"
            className={`story-card story-card--station ${activeCode === s.code ? 'story-card--on' : ''}`}
            onClick={() => onSelect?.({ type: 'station', id: s.code, name: s.name, basin: s.basin })}
          >
            <span className={`story-card__status story-card__status--${s.status}`}>
              {t(STATUS_LABEL[s.status])}
            </span>
            <h3 className="story-card__title">{s.name}</h3>
            <p className="story-card__meta">{s.region} · {s.basin}</p>
            <div className="story-card__metric">
              <span>WQI</span>
              <strong>{s.mean_wqi}</strong>
            </div>
            <p className="story-card__insight">{s.records.toLocaleString()} {t('map.hoverRecords').toLowerCase()}</p>
          </button>
        ))}
      </div>
    </div>
  )
}
