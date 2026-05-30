import React from 'react'
import { useLanguage } from '../../i18n/LanguageContext.jsx'

const LAYERS = [
  { id: 'wqi', enabled: true },
  { id: 'hotspot', enabled: true },
  { id: 'pollution', enabled: true },
  { id: 'basins', enabled: true },
]

export function MapLayerControl({ mapMode, onMapModeChange }) {
  const { t } = useLanguage()
  return (
    <div className="map-layers" role="group" aria-label={t('map.layersTitle')}>
      <span className="map-layers__label">{t('map.layersTitle')}</span>
      <div className="map-layers__buttons">
        {LAYERS.map(({ id, enabled }) => (
          <button
            key={id}
            type="button"
            className={`map-layers__btn ${mapMode === id ? 'map-layers__btn--on' : ''}`}
            disabled={!enabled}
            title={!enabled ? t('map.layerDisabled') : undefined}
            onClick={() => enabled && onMapModeChange(id)}
          >
            {t(`map.mode.${id}`)}
          </button>
        ))}
      </div>
    </div>
  )
}
