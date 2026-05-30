import React from 'react'
import { useLanguage } from '../../i18n/LanguageContext.jsx'
import { useSectionReveal } from '../../hooks/useSectionReveal.js'
import { AnimatedNumber } from '../ui/AnimatedNumber.jsx'

export function RiskDashboard({ riskAlerts, inline = false }) {
  const { t } = useLanguage()
  const { ref, className } = useSectionReveal()
  if (!riskAlerts) return null

  const inner = (
    <>
      <div className="risk-summary" style={inline ? { marginTop: '1rem' } : undefined}>
        <div className="risk-box risk-box--crit" style={inline ? { background: 'rgba(0,0,0,0.25)', borderRadius: 12, padding: '0.75rem 1rem' } : undefined}>
          <span>{t('overview.highRisk')}</span>
          <strong><AnimatedNumber value={riskAlerts.high_risk_count} decimals={0} /></strong>
          <em>{t('overview.ofSample', { pct: riskAlerts.high_risk_pct })}</em>
        </div>
        <div className="risk-box risk-box--warn" style={inline ? { background: 'rgba(0,0,0,0.25)', borderRadius: 12, padding: '0.75rem 1rem' } : undefined}>
          <span>{t('overview.modRisk')}</span>
          <strong><AnimatedNumber value={riskAlerts.moderate_risk_count} decimals={0} /></strong>
          <em>{t('overview.ofSample', { pct: riskAlerts.moderate_risk_pct })}</em>
        </div>
      </div>
      <div className="risk-table-wrap" style={inline ? { marginTop: '1rem', background: 'rgba(0,0,0,0.2)', borderRadius: 12, overflow: 'auto' } : undefined}>
        <table className="forecast-table">
          <thead>
            <tr>
              <th>{t('overview.thRegion')}</th>
              <th>{t('overview.thHighRisk')}</th>
              <th>{t('overview.thShare')}</th>
              <th>{t('overview.thMeanRatio')}</th>
              <th>{t('overview.thMeanWqi')}</th>
            </tr>
          </thead>
          <tbody>
            {(Array.isArray(riskAlerts.top_regions) ? riskAlerts.top_regions : []).map((r) => (
              <tr key={r.Region}>
                <td>{r.Region}</td>
                <td>{r.High_Risk_Records}</td>
                <td>{r['High_Risk_Share_%']}%</td>
                <td>{r.Mean_Ratio?.toFixed(2)}</td>
                <td>{r.Mean_WQI?.toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )

  if (inline) return inner

  return (
    <section id="risk" ref={ref} className={className}>
      <p className="section__eyebrow">{t('overview.riskTitle')}</p>
      <h2 className="section__title">{t('overview.riskSubtitle', { count: riskAlerts.high_risk_count })}</h2>
      {inner}
    </section>
  )
}
