/** Slice trend chart traces up to a focus year and add a vertical marker */
export function focusTrendByYear(figure, yearFocus) {
  if (!figure?.data?.length || yearFocus == null) return figure

  const data = figure.data.map((trace) => {
    const xs = Array.isArray(trace.x) ? trace.x : []
    const ys = Array.isArray(trace.y) ? trace.y : []
    const pairs = xs
      .map((x, i) => ({ x: Number(x), y: ys[i] }))
      .filter((p) => !Number.isNaN(p.x) && p.x <= yearFocus)
    return { ...trace, x: pairs.map((p) => p.x), y: pairs.map((p) => p.y) }
  })

  const marker = {
    type: 'line',
    x0: yearFocus,
    x1: yearFocus,
    y0: 0,
    y1: 1,
    xref: 'x',
    yref: 'paper',
    line: { color: 'rgba(34, 211, 238, 0.55)', width: 1.5, dash: 'dot' },
  }

  return {
    ...figure,
    data,
    layout: {
      ...(figure.layout && typeof figure.layout === 'object' ? figure.layout : {}),
      shapes: [...(figure.layout?.shapes || []), marker],
    },
  }
}
