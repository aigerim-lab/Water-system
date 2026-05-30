import React from 'react'
import { useLanguage } from '../../i18n/LanguageContext.jsx'

export function LakeStoryGrid({ lakeStats = [], onSelect }) {
  const { t } = useLanguage()
  if (!lakeStats.length) return null

  return (
    <div className="story-grid story-grid--lakes">
      {lakeStats.map((lake) => (
        <button
          key={lake.id}
          type="button"
          className="story-card story-card--lake"
          onClick={() => onSelect?.({ type: 'lake', id: lake.id, name: lake.name, basin: lake.basin })}
        >
          <span className="story-card__eyebrow">{t('gis.lake')}</span>
          <h3 className="story-card__title">{lake.name}</h3>
          <p className="story-card__meta">{lake.basin} · {lake.area_km2?.toLocaleString()} km²</p>
          <div className="story-card__lake-surface" aria-hidden="true">
            <span className="story-card__ripple" />
          </div>
          {lake.mean_wqi != null && (
            <div className="story-card__metric">
              <span>{t('map.hoverWqi')}</span>
              <strong>{lake.mean_wqi}</strong>
            </div>
          )}
          {lake.top_pollutant && (
            <p className="story-card__insight">{lake.top_pollutant}</p>
          )}
        </button>
      ))}
    </div>
  )
}
