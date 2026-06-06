import React from 'react'
import { LazyPlot } from '../LazyPlot.jsx'
import { useLanguage } from '../../i18n/LanguageContext.jsx'

export function ChartPanel({ title, subtitle, figure, plotLayout, narrative, tall = false, chartKey }) {
  const { t } = useLanguage()
  const hasData = figure && Array.isArray(figure.data) && figure.data.length > 0
  const gridColor = plotLayout?.gridColor
  const hasHeader = Boolean(title || subtitle)
  const chartMargin = figure?.layout?.margin ?? { t: 32, r: 20, b: 48, l: 56 }

  return (
    <article className="chart-panel glass-panel">
      {hasHeader && (
        <header className="chart-panel__head">
          {title && <h3 className="chart-panel__title">{title}</h3>}
          {subtitle && <p className="chart-panel__sub">{subtitle}</p>}
        </header>
      )}
      <div className="chart-panel__body">
        {hasData ? (
          <LazyPlot
            key={chartKey}
            data={figure.data}
            layout={{
              ...(figure.layout && typeof figure.layout === 'object' ? figure.layout : {}),
              autosize: true,
              title: undefined,
              template: undefined,
              paper_bgcolor: plotLayout?.paper_bgcolor ?? 'transparent',
              plot_bgcolor: plotLayout?.plot_bgcolor ?? 'transparent',
              font: plotLayout?.font,
              margin: chartMargin,
              xaxis: {
                ...(figure.layout?.xaxis || {}),
                gridcolor: gridColor,
                tickfont: { color: plotLayout?.font?.color, size: 10 },
              },
              yaxis: {
                ...(figure.layout?.yaxis || {}),
                gridcolor: gridColor,
                tickfont: { color: plotLayout?.font?.color, size: 10 },
              },
            }}
            config={{ responsive: true, displayModeBar: true, displaylogo: false, modeBarButtonsToRemove: ['lasso2d', 'select2d'] }}
            style={{ width: '100%', height: tall ? 380 : 300 }}
            useResizeHandler
          />
        ) : (
          <p className="empty-state chart-panel__empty">{t('empty.noCharts')}</p>
        )}
      </div>
      {narrative && hasData && <p className="chart-narrative">{narrative}</p>}
    </article>
  )
}
