import React, { useState } from 'react'
import { useLanguage } from '../../i18n/LanguageContext.jsx'
import { SmartFilterRail } from './SmartFilterRail.jsx'
import { asArray } from '../../utils/array.js'

export function EnvironmentalExplorer({ options, filters, onChange, onReset }) {
  const { t } = useLanguage()
  const [open, setOpen] = useState(false)

  const scopeParts = [
    asArray(filters.basins).length === asArray(options.basins).length
      ? t('filters.all')
      : t('filters.of', { n: asArray(filters.basins).length, total: asArray(options.basins).length }),
    asArray(filters.years).length
      ? `${Math.min(...asArray(filters.years))}–${Math.max(...asArray(filters.years))}`
      : '—',
    asArray(filters.regions).length === asArray(options.regions).length
      ? t('journey.scopeAllRegions')
      : t('filters.of', { n: asArray(filters.regions).length, total: asArray(options.regions).length }),
  ]

  return (
    <>
      <div className="env-scope" aria-live="polite">
        <button
          type="button"
          className="env-scope__toggle"
          onClick={() => setOpen((o) => !o)}
          aria-expanded={open}
        >
          <span className="env-scope__icon" aria-hidden="true">◎</span>
          <span className="env-scope__label">{t('journey.exploreData')}</span>
          <span className="env-scope__summary">{scopeParts.join(' · ')}</span>
        </button>
      </div>

      <div className={`env-panel ${open ? 'env-panel--open' : ''}`} role="dialog" aria-label={t('filters.title')}>
        <header className="env-panel__head">
          <div>
            <h2 className="env-panel__title">{t('journey.filterTitle')}</h2>
            <p className="env-panel__sub">{t('journey.filterSub')}</p>
          </div>
          <button type="button" className="env-panel__close" onClick={() => setOpen(false)} aria-label={t('filters.close')}>×</button>
        </header>
        <div className="env-panel__body">
          <SmartFilterRail options={options} filters={filters} onChange={onChange} onReset={onReset} expanded />
        </div>
      </div>
      {open && <button type="button" className="env-panel__backdrop" onClick={() => setOpen(false)} aria-label={t('filters.close')} />}
    </>
  )
}
