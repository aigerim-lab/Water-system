import React, { Suspense } from 'react'

const Plot = React.lazy(() => import('react-plotly.js'))

export function LazyPlot(props) {
  const hasData = Array.isArray(props?.data) && props.data.length > 0
  return (
    <Suspense fallback={<div className="chart-skeleton" aria-hidden="true" />}>
      {hasData ? <Plot {...props} /> : <div className="chart-skeleton" aria-hidden="true" />}
    </Suspense>
  )
}
