import React, { useEffect, useState } from 'react'
import { api } from '../../api.js'
import { useLanguage } from '../../i18n/LanguageContext.jsx'
import { useSectionReveal } from '../../hooks/useSectionReveal.js'
import { safeRegions, safeYears } from '../../utils/array.js'

export function PeriodCompare({ filters, regions, years, teaser, inline = false }) {
  const { t } = useLanguage()
  const { ref, className } = useSectionReveal()
  const regionList = safeRegions(regions)
  const yearList = safeYears(years)
  const [compare, setCompare] = useState({
    region_a: regionList[0] || '',
    year_a: yearList[0] || 2020,
    region_b: regionList[1] || regionList[0] || '',
    year_b: yearList[yearList.length - 1] || 2024,
  })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!regionList.length || !yearList.length) return
    setCompare({
      region_a: regionList[0],
      year_a: yearList[0],
      region_b: regionList[Math.min(1, regionList.length - 1)],
      year_b: yearList[yearList.length - 1],
    })
    setResult(null)
    setError(null)
  }, [regionList.join('|'), yearList.join('|'), JSON.stringify(filters ?? {})])

  const run = () => {
    setLoading(true)
    setError(null)
    api.compare({ ...filters, ...compare })
      .then((res) => {
        if (res?.ok) setResult(res)
        else {
          setResult(null)
          setError(t('compare.error'))
        }
      })
      .catch(() => {
        setResult(null)
        setError(t('compare.error'))
      })
      .finally(() => setLoading(false))
  }

  const panel = (
      <div className="compare-panel" style={inline ? { background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '12px' } : undefined}>
        <div className="compare-row">
          <div className="compare-slot">
            <label>{t('compare.periodA')}</label>
            <select value={compare.region_a} onChange={(e) => setCompare({ ...compare, region_a: e.target.value })}>
              {regionList.map((r) => <option key={r}>{r}</option>)}
            </select>
            <select value={compare.year_a} onChange={(e) => setCompare({ ...compare, year_a: Number(e.target.value) })}>
              {yearList.map((y) => <option key={y}>{y}</option>)}
            </select>
          </div>
          <div className="compare-vs">{t('compare.vs')}</div>
          <div className="compare-slot">
            <label>{t('compare.periodB')}</label>
            <select value={compare.region_b} onChange={(e) => setCompare({ ...compare, region_b: e.target.value })}>
              {regionList.map((r) => <option key={r}>{r}</option>)}
            </select>
            <select value={compare.year_b} onChange={(e) => setCompare({ ...compare, year_b: Number(e.target.value) })}>
              {yearList.map((y) => <option key={y}>{y}</option>)}
            </select>
          </div>
        </div>
        <button type="button" className="btn-primary" onClick={run} disabled={loading}>
          {loading ? t('compare.loading') : t('compare.submit')}
        </button>
        {error && <p className="alert-error" style={{ marginTop: '0.75rem' }}>{error}</p>}
        {result?.ok && (
          <div className="delta-grid">
            <div className="delta-card">
              <span>{t('compare.wqiChange')}</span>
              <strong className={result.wqi_delta > 0 ? 'up' : 'down'}>
                {result.wqi_delta > 0 ? '+' : ''}{result.wqi_delta}
              </strong>
            </div>
            <div className="delta-card">
              <span>{t('compare.pollutionChange')}</span>
              <strong>{result.ratio_delta}</strong>
            </div>
            <div className="delta-card">
              <span>{t('compare.riskChange')}</span>
              <strong>{result.high_risk_delta_pp} {t('compare.pp')}</strong>
            </div>
          </div>
        )}
      </div>
  )

  if (inline) return panel

  return (
    <section id="compare" ref={ref} className={className}>
      <p className="section__eyebrow">{t('sections.compare.eyebrow')}</p>
      <h2 className="section__title">{t('sections.compare.title')}</h2>
      <p className="section__lead">{teaser || t('sections.compare.lead')}</p>
      {panel}
    </section>
  )
}
