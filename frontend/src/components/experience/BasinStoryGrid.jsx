import React from 'react'
import { useLanguage } from '../../i18n/LanguageContext.jsx'

export function BasinStoryGrid({ basinStats = [], onSelect, activeBasin }) {
  const { t } = useLanguage()
  if (!basinStats.length) return null

  return (
    <div className="story-grid story-grid--basins">
      {basinStats.map((b) => {
        const trend = b.trend_wqi_delta
        const trendDir = trend == null ? 'flat' : trend > 0 ? 'up' : trend < 0 ? 'down' : 'flat'
        return (
          <button
            key={b.id}
            type="button"
            className={`story-card story-card--basin ${activeBasin === b.id ? 'story-card--on' : ''}`}
            onClick={() => onSelect?.(b.id)}
          >
            <span className="story-card__eyebrow">{t('gis.basin')}</span>
            <h3 className="story-card__title">{b.id.replace(/-/g, ' ')}</h3>
            <div className="story-card__metric">
              <span>WQI</span>
              <strong>{b.mean_wqi}</strong>
            </div>
            <div className={`story-card__flow story-card__flow--${trendDir}`} aria-hidden="true">
              <span className="story-card__flow-track" />
            </div>
            <p className="story-card__insight">
              {t('gis.topRegion')}: <strong>{b.top_region}</strong> · {b.top_pollutant}
            </p>
            {trend != null && (
              <span className={`story-card__trend story-card__trend--${trendDir}`}>
                {trend > 0 ? '+' : ''}{trend} {t('gis.trend')}
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}
