import React, { useCallback, useEffect, useMemo, useState } from 'react'
import Plot from 'react-plotly.js'
import { api } from './api.js'
import { useLanguage } from './i18n/LanguageContext.jsx'
import { LanguageSwitcher } from './i18n/LanguageSwitcher.jsx'
import { ChatPanel } from './components/ChatPanel.jsx'

const DEFAULT_SOURCES = ['observed', 'reconstructed']

const MODULE_IDS = [
  { id: 'overview', image: '/images/hero-overview.svg' },
  { id: 'analytics', image: '/images/hero-analytics.svg' },
  { id: 'ml', image: '/images/hero-forecast.svg' },
  { id: 'compare', image: '/images/hero-compare.svg' },
]

const NAV_KEYS = {
  overview: 'nav.overview',
  analytics: 'nav.analytics',
  ml: 'nav.ml',
  compare: 'nav.compare',
}

const PLOT_LAYOUT = {
  paper_bgcolor: 'transparent',
  plot_bgcolor: 'transparent',
  font: { family: 'Inter, sans-serif', color: '#8b949e', size: 11 },
  margin: { t: 24, r: 12, b: 36, l: 44 },
  colorway: ['#4dabf7', '#51cf66', '#ffd43b', '#ff6b6b', '#74c0fc'],
}

function FilterGroup({ label, options, selected, onChange, sourceLabels, allLabel, clearLabel }) {
  const toggle = (val) => {
    if (selected.includes(val)) onChange(selected.filter((x) => x !== val))
    else onChange([...selected, val])
  }

  return (
    <div className="filter-group">
      <div className="filter-label-row">
        <span className="filter-label">{label}</span>
        <span className="filter-actions">
          <button type="button" onClick={() => onChange([...options])}>{allLabel}</button>
          <button type="button" onClick={() => onChange([])}>{clearLabel}</button>
        </span>
      </div>
      <div className="tag-list">
        {options.map((o) => (
          <button
            key={o}
            type="button"
            className={`tag ${selected.includes(o) ? 'on' : ''}`}
            onClick={() => toggle(o)}
          >
            {sourceLabels[o] || o}
          </button>
        ))}
      </div>
    </div>
  )
}

function HudPanel({ title, subtitle, children, chart = false }) {
  return (
    <section className="panel">
      <header className="panel-head">
        <div>
          <div className="panel-title">{title}</div>
          {subtitle && <div className="panel-sub">{subtitle}</div>}
        </div>
      </header>
      <div className={`panel-body ${chart ? 'panel-body--chart' : ''}`}>{children}</div>
    </section>
  )
}

function ChartPanel({ title, subtitle, figure, tall = false }) {
  if (!figure) return null
  return (
    <HudPanel title={title} subtitle={subtitle} chart>
      <Plot
        data={figure.data}
        layout={{
          ...figure.layout,
          ...PLOT_LAYOUT,
          autosize: true,
          title: undefined,
          xaxis: { ...figure.layout?.xaxis, gridcolor: 'rgba(255,255,255,0.06)', tickfont: { color: '#8b949e', size: 10 } },
          yaxis: { ...figure.layout?.yaxis, gridcolor: 'rgba(255,255,255,0.06)', tickfont: { color: '#8b949e', size: 10 } },
        }}
        config={{ responsive: true, displayModeBar: false, displaylogo: false }}
        style={{ width: '100%', height: tall ? 420 : 300 }}
        useResizeHandler
      />
    </HudPanel>
  )
}

function ModuleHero({ tag, title, desc, meta, image }) {
  return (
    <header className="module-hero">
      <div>
        <div className="mod-tag">{tag}</div>
        <h1 className="mod-title">{title}</h1>
        {desc && <p className="mod-desc">{desc}</p>}
        {meta && <div className="mod-meta">{meta}</div>}
      </div>
      {image && <img src={image} alt="" className="module-hero-art" />}
    </header>
  )
}

export default function App() {
  const { t, locale } = useLanguage()

  const [meta, setMeta] = useState(null)
  const [options, setOptions] = useState({ regions: [], years: [], pollutants: [], sources: [] })
  const [filters, setFilters] = useState({ sources: DEFAULT_SOURCES, regions: [], years: [], pollutants: [] })
  const [summary, setSummary] = useState(null)
  const [charts, setCharts] = useState(null)
  const [ml, setMl] = useState(null)
  const [mlTarget, setMlTarget] = useState('WQI_Score')
  const [compare, setCompare] = useState({ region_a: '', year_a: 2020, region_b: '', year_b: 2024 })
  const [compareResult, setCompareResult] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeModule, setActiveModule] = useState('overview')
  const [filtersOpen, setFiltersOpen] = useState(true)
  const [chatOpen, setChatOpen] = useState(false)

  const sourceLabels = useMemo(() => ({
    observed: t('sources.observed'),
    reconstructed: t('sources.reconstructed'),
    reference: t('sources.reference'),
  }), [t])

  const activeImage = MODULE_IDS.find((m) => m.id === activeModule)?.image

  const body = useCallback(
    () => ({
      sources: filters.sources.length ? filters.sources : undefined,
      regions: filters.regions.length ? filters.regions : undefined,
      years: filters.years.length ? filters.years : undefined,
      pollutants: filters.pollutants.length ? filters.pollutants : undefined,
    }),
    [filters]
  )

  useEffect(() => {
    api.meta().then(setMeta).catch((e) => setError(e.message))
    api.filterOptions({ sources: DEFAULT_SOURCES })
      .then((opts) => {
        setOptions(opts)
        setFilters({
          sources: DEFAULT_SOURCES.filter((s) => opts.sources.includes(s)),
          regions: opts.regions,
          years: opts.years,
          pollutants: opts.pollutants,
        })
      })
      .catch((e) => setError(e.message))
  }, [])

  useEffect(() => {
    if (!filters.regions.length) return
    setLoading(true)
    setError(null)
    const payload = body()
    Promise.all([api.summary(payload), api.charts(payload), api.ml(payload, mlTarget)])
      .then(([sum, ch, mlRes]) => {
        setSummary(sum)
        setCharts(ch)
        setMl(mlRes)
        setCompare((c) => ({
          region_a: c.region_a || filters.regions[0],
          region_b: c.region_b || filters.regions[1] || filters.regions[0],
          year_a: c.year_a || filters.years[0],
          year_b: c.year_b || filters.years[filters.years.length - 1],
        }))
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [filters, mlTarget, body])

  const updateFilter = (key, val) => {
    setFilters((f) => {
      const next = { ...f, [key]: val }
      if (key === 'sources') api.filterOptions({ sources: val }).then(setOptions)
      return next
    })
  }

  const resetFilters = () =>
    setFilters({
      sources: DEFAULT_SOURCES.filter((s) => options.sources.includes(s)),
      regions: options.regions,
      years: options.years,
      pollutants: options.pollutants,
    })

  const filterSummary = useMemo(() => [
    {
      k: t('filters.chipSource'),
      v: filters.sources.map((s) => sourceLabels[s] || s).join(', ') || '—',
    },
    {
      k: t('filters.chipRegions'),
      v: t('filters.of', { n: filters.regions.length, total: options.regions.length }),
    },
    {
      k: t('filters.chipYears'),
      v: t('filters.of', { n: filters.years.length, total: options.years.length }),
    },
    {
      k: t('filters.chipPollutants'),
      v: t('filters.of', { n: filters.pollutants.length, total: options.pollutants.length }),
    },
  ], [filters, options, sourceLabels, t])

  const ts = new Date().toLocaleString(locale, {
    hour: '2-digit',
    minute: '2-digit',
    day: '2-digit',
    month: 'short',
  })

  const recordCount = summary?.kpi?.records?.toLocaleString(locale) ?? '—'

  return (
    <div className="ops">
      <div className="grid-bg" aria-hidden="true" />
      <div className="bg-art" aria-hidden="true" />

      <header className="command-bar">
        <div className="brand">
          <div className="brand-sigil">
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M12 3C12 3 6 11 6 16a6 6 0 0012 0c0-5-6-13-6-13z" fill="#4dabf7" opacity="0.9" />
            </svg>
          </div>
          <div className="brand-text">
            <div className="brand-name">AquaMonitor</div>
            <div className="brand-sub">{t('brandSub')}</div>
          </div>
        </div>

        <nav className="module-nav">
          {MODULE_IDS.map((m) => (
            <button
              key={m.id}
              type="button"
              className={`module-tab ${activeModule === m.id ? 'active' : ''}`}
              onClick={() => setActiveModule(m.id)}
            >
              {t(NAV_KEYS[m.id])}
            </button>
          ))}
        </nav>

        <div className="command-right">
          <LanguageSwitcher />
          <div className="status-cluster">
            <span className="status-item">
              <span className={`status-led ${loading ? 'status-led--load' : ''}`} />
              {loading ? t('status.updating') : t('status.current')}
            </span>
          </div>
          <button
            type="button"
            className="btn-ops btn-ops--solid"
            onClick={async () => {
              const blob = await api.exportCsv(body())
              const url = URL.createObjectURL(blob)
              const a = document.createElement('a')
              a.href = url
              a.download = 'water_quality_export.csv'
              a.click()
            }}
          >
            {t('exportCsv')}
          </button>
        </div>
      </header>

      <div className="query-bar">
        <div className="query-toggle-row">
          <button
            type="button"
            className="query-toggle"
            onClick={() => setFiltersOpen((o) => !o)}
          >
            <span className={`query-toggle-icon ${filtersOpen ? 'open' : ''}`}>▸</span>
            {t('filters.title')}
          </button>
          <div className="query-summary">
            {filterSummary.map(({ k, v }) => (
              <span key={k} className="query-chip"><strong>{k}:</strong> {v}</span>
            ))}
            <button type="button" className="query-reset" onClick={resetFilters}>{t('filters.resetAll')}</button>
          </div>
        </div>
        {filtersOpen && (
          <div className="query-panel">
            <FilterGroup
              label={t('filters.source')}
              options={options.sources}
              selected={filters.sources}
              onChange={(v) => updateFilter('sources', v)}
              sourceLabels={sourceLabels}
              allLabel={t('filters.all')}
              clearLabel={t('filters.clear')}
            />
            <FilterGroup
              label={t('filters.region')}
              options={options.regions}
              selected={filters.regions}
              onChange={(v) => updateFilter('regions', v)}
              sourceLabels={{}}
              allLabel={t('filters.all')}
              clearLabel={t('filters.clear')}
            />
            <FilterGroup
              label={t('filters.year')}
              options={options.years}
              selected={filters.years}
              onChange={(v) => updateFilter('years', v)}
              sourceLabels={{}}
              allLabel={t('filters.all')}
              clearLabel={t('filters.clear')}
            />
            <FilterGroup
              label={t('filters.pollutant')}
              options={options.pollutants}
              selected={filters.pollutants}
              onChange={(v) => updateFilter('pollutants', v)}
              sourceLabels={{}}
              allLabel={t('filters.all')}
              clearLabel={t('filters.clear')}
            />
          </div>
        )}
      </div>

      {loading && (
        <div className="loader-track">
          <div className="loader-fill" />
        </div>
      )}

      {meta && (
        <div className="alert-strip">
          <span className="alert-strip-icon">ℹ</span>
          <span>{meta.banner}</span>
        </div>
      )}

      {error && (
        <div className="alert-error">{t('errors.loadFailed')} {error}</div>
      )}

      <main className="viewport">
        {activeModule === 'overview' && summary && (
          <>
            <ModuleHero
              tag={t('overview.tag')}
              title={t('overview.title')}
              desc={t('overview.desc')}
              meta={t('overview.meta', {
                count: summary.kpi.records.toLocaleString(locale),
                wqi: summary.kpi.mean_wqi,
              })}
              image={activeImage}
            />

            <div className="kpi-strip">
              <div className="kpi">
                <div className="kpi-label">{t('overview.kpiRecords')}</div>
                <div className="kpi-value">{summary.kpi.records.toLocaleString(locale)}</div>
              </div>
              <div className="kpi">
                <div className="kpi-label">{t('overview.kpiWqi')}</div>
                <div className="kpi-value">{summary.kpi.mean_wqi}</div>
              </div>
              <div className="kpi">
                <div className="kpi-label">{t('overview.kpiPollution')}</div>
                <div className="kpi-value">
                  {summary.kpi.mean_ratio}
                  <span className="kpi-unit">{t('overview.mpcUnit')}</span>
                </div>
              </div>
              <div className={`kpi ${summary.kpi.high_risk_share > 30 ? 'kpi--crit' : 'kpi--warn'}`}>
                <div className="kpi-label">{t('overview.kpiHighRisk')}</div>
                <div className="kpi-value">{summary.kpi.high_risk_share}<span className="kpi-unit">%</span></div>
              </div>
              <div className="kpi kpi--ok">
                <div className="kpi-label">{t('overview.kpiObserved')}</div>
                <div className="kpi-value">{summary.data_quality.observed_pct || 0}<span className="kpi-unit">%</span></div>
              </div>
              <div className="kpi">
                <div className="kpi-label">{t('overview.kpiReconstructed')}</div>
                <div className="kpi-value">{summary.data_quality.reconstructed_pct || 0}<span className="kpi-unit">%</span></div>
              </div>
              <div className="kpi">
                <div className="kpi-label">{t('overview.kpiReference')}</div>
                <div className="kpi-value">{summary.data_quality.reference_pct || 0}<span className="kpi-unit">%</span></div>
              </div>
            </div>

            <div className="grid-2-1">
              <HudPanel
                title={t('overview.riskTitle')}
                subtitle={t('overview.riskSubtitle', { count: summary.risk_alerts.high_risk_count })}
              >
                <div className="threat-row">
                  <div className="threat threat--crit">
                    <div className="threat-label">{t('overview.highRisk')}</div>
                    <div className="threat-num">{summary.risk_alerts.high_risk_count}</div>
                    <div className="threat-sub">{t('overview.ofSample', { pct: summary.risk_alerts.high_risk_pct })}</div>
                  </div>
                  <div className="threat threat--warn">
                    <div className="threat-label">{t('overview.modRisk')}</div>
                    <div className="threat-num">{summary.risk_alerts.moderate_risk_count}</div>
                    <div className="threat-sub">{t('overview.ofSample', { pct: summary.risk_alerts.moderate_risk_pct })}</div>
                  </div>
                </div>
                <div className="tbl-wrap">
                  <table>
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
                      {summary.risk_alerts.top_regions.map((r) => (
                        <tr key={r.Region}>
                          <td className="td-name">{r.Region}</td>
                          <td className="num">{r.High_Risk_Records}</td>
                          <td><span className="badge badge--neutral">{r['High_Risk_Share_%']}%</span></td>
                          <td className="num">{r.Mean_Ratio?.toFixed(2)}</td>
                          <td className="num">{r.Mean_WQI?.toFixed(1)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </HudPanel>

              <HudPanel title={t('overview.insightsTitle')} subtitle={t('overview.insightsSub')}>
                <div className="intel-feed">
                  {summary.insights.slice(0, -1).map((line, i) => (
                    <div
                      key={i}
                      className="intel-item"
                      dangerouslySetInnerHTML={{
                        __html: line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>'),
                      }}
                    />
                  ))}
                  <p className="intel-foot">{summary.insights.at(-1)}</p>
                </div>
              </HudPanel>
            </div>
          </>
        )}

        {activeModule === 'analytics' && charts && (
          <>
            <ModuleHero
              tag={t('analytics.tag')}
              title={t('analytics.title')}
              desc={t('analytics.desc')}
              image={activeImage}
            />
            <ChartPanel title={t('analytics.mapTitle')} subtitle={t('analytics.mapSub')} figure={charts.map} tall />
            <div className="grid-2">
              <ChartPanel title={t('analytics.trendTitle')} subtitle={t('analytics.trendSub')} figure={charts.trend} />
              <ChartPanel title={t('analytics.rankTitle')} subtitle={t('analytics.rankSub')} figure={charts.regions} />
            </div>
            <ChartPanel title={t('analytics.matrixTitle')} subtitle={t('analytics.matrixSub')} figure={charts.heatmap} tall />
            <ChartPanel title={t('analytics.yoyTitle')} subtitle={t('analytics.yoySub')} figure={charts.yoy_delta} />
          </>
        )}

        {activeModule === 'ml' && ml?.ok && (
          <>
            <ModuleHero
              tag={t('ml.tag')}
              title={t('ml.title')}
              desc={meta?.ml_disclaimer}
              meta={t('ml.meta', { year: ml.forecast_year })}
              image={activeImage}
            />
            <HudPanel title={t('ml.panelTitle')}>
              <div className="seg">
                {['WQI_Score', 'Concentration'].map((target) => (
                  <button
                    key={target}
                    type="button"
                    className={mlTarget === target ? 'active' : ''}
                    onClick={() => setMlTarget(target)}
                  >
                    {target === 'WQI_Score' ? t('ml.targetWqi') : t('ml.targetConc')}
                  </button>
                ))}
              </div>
              {ml.any_overfitting && (
                <div className="warn-box">{t('ml.overfitWarn')}</div>
              )}
              <div className="tbl-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>{t('ml.thModel')}</th>
                      <th>{t('ml.thForecast', { year: ml.forecast_year })}</th>
                      <th>CV MAE</th>
                      <th>CV R²</th>
                      <th>CV MAPE</th>
                      <th>{t('ml.thOverfit')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ml.comparison_table.map((row) => (
                      <tr key={row.Model} className={row.Rank === 1 ? 'row-active' : ''}>
                        <td className="num">{row.Rank}</td>
                        <td className="td-name">{row.Model}</td>
                        <td className="num">{row[`Pred ${ml.forecast_year}`]}</td>
                        <td className="num">{row['CV MAE']}</td>
                        <td className="num">{row['CV R²']}</td>
                        <td className="num">{row['CV MAPE %']}%</td>
                        <td>
                          {row['Overfit ⚠'] === 'Yes' ? (
                            <span className="badge badge--crit">{t('ml.yes')}</span>
                          ) : (
                            <span className="badge badge--ok">{t('ml.no')}</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="footnote">{meta?.why_not_deep_learning}</p>
            </HudPanel>
          </>
        )}

        {activeModule === 'ml' && ml && !ml.ok && (
          <ModuleHero
            tag={t('ml.tag')}
            title={t('ml.unavailableTitle')}
            desc={t('ml.unavailableDesc')}
            image={activeImage}
          />
        )}

        {activeModule === 'compare' && (
          <>
            <ModuleHero
              tag={t('compare.tag')}
              title={t('compare.title')}
              desc={t('compare.desc')}
              image={activeImage}
            />
            <HudPanel title={t('compare.panelTitle')}>
              <div className="compare-row">
                <div className="compare-slot">
                  <label>{t('compare.periodA')}</label>
                  <select value={compare.region_a} onChange={(e) => setCompare({ ...compare, region_a: e.target.value })}>
                    {filters.regions.map((r) => <option key={r}>{r}</option>)}
                  </select>
                  <select value={compare.year_a} onChange={(e) => setCompare({ ...compare, year_a: Number(e.target.value) })}>
                    {filters.years.map((y) => <option key={y}>{y}</option>)}
                  </select>
                </div>
                <div className="compare-vs">{t('compare.vs')}</div>
                <div className="compare-slot">
                  <label>{t('compare.periodB')}</label>
                  <select value={compare.region_b} onChange={(e) => setCompare({ ...compare, region_b: e.target.value })}>
                    {filters.regions.map((r) => <option key={r}>{r}</option>)}
                  </select>
                  <select value={compare.year_b} onChange={(e) => setCompare({ ...compare, year_b: Number(e.target.value) })}>
                    {filters.years.map((y) => <option key={y}>{y}</option>)}
                  </select>
                </div>
              </div>
              <button
                type="button"
                className="btn-ops btn-ops--solid"
                onClick={() => api.compare({ ...body(), ...compare }).then(setCompareResult).catch((e) => setError(e.message))}
              >
                {t('compare.submit')}
              </button>
              {compareResult?.ok && (
                <div className="delta-strip">
                  <div className="delta">
                    <span>{t('compare.wqiChange')}</span>
                    <strong className={compareResult.wqi_delta > 0 ? 'up' : 'down'}>
                      {compareResult.wqi_delta > 0 ? '+' : ''}{compareResult.wqi_delta}
                    </strong>
                  </div>
                  <div className="delta">
                    <span>{t('compare.pollutionChange')}</span>
                    <strong>{compareResult.ratio_delta}</strong>
                  </div>
                  <div className="delta">
                    <span>{t('compare.riskChange')}</span>
                    <strong>{compareResult.high_risk_delta_pp} {t('compare.pp')}</strong>
                  </div>
                </div>
              )}
            </HudPanel>
          </>
        )}
      </main>

      <footer className="status-bar">
        <div className="status-bar-left">
          <span>{t('footer.thesis')}</span>
          <span>{t('footer.standards')}</span>
        </div>
        <div className="status-bar-right">
          <span>{ts}</span>
          <span>{t('footer.records', { count: recordCount })}</span>
        </div>
      </footer>

      <ChatPanel
        filters={body()}
        open={chatOpen}
        onToggle={() => setChatOpen((o) => !o)}
      />
    </div>
  )
}
