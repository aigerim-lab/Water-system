/** Read Plotly trace axis values (plain arrays or legacy binary bdata). */
export function plotlyValues(val) {
  if (Array.isArray(val)) return val
  if (val && typeof val === 'object' && val.bdata && val.dtype) {
    const binary = atob(val.bdata)
    const buf = new ArrayBuffer(binary.length)
    const view = new Uint8Array(buf)
    for (let i = 0; i < binary.length; i++) view[i] = binary.charCodeAt(i)
    if (val.dtype === 'f8') return Array.from(new Float64Array(buf))
    if (val.dtype === 'f4') return Array.from(new Float32Array(buf))
    if (val.dtype === 'i4') return Array.from(new Int32Array(buf))
    if (val.dtype === 'i2') return Array.from(new Int16Array(buf))
  }
  return []
}

const FOCUS_SHAPE = 'aquamonitor-year-focus'

/** Highlight focus year on trend chart without stripping trace data. */
export function focusTrendByYear(figure, yearFocus) {
  if (!figure?.data?.length || yearFocus == null) return figure

  const focusYear = Number(yearFocus)
  if (Number.isNaN(focusYear)) return figure

  const xs = plotlyValues(figure.data[0]?.x)
  const xMin = xs.length ? Math.min(...xs.map(Number)) : focusYear

  const prevShapes = (figure.layout?.shapes || []).filter((s) => s?.name !== FOCUS_SHAPE)

  return {
    ...figure,
    layout: {
      ...(figure.layout && typeof figure.layout === 'object' ? figure.layout : {}),
      xaxis: {
        ...(figure.layout?.xaxis || {}),
        range: [xMin - 0.5, Math.max(focusYear + 0.5, xMin + 1)],
        autorange: false,
      },
      shapes: [
        ...prevShapes,
        {
          type: 'line',
          name: FOCUS_SHAPE,
          x0: focusYear,
          x1: focusYear,
          y0: 0,
          y1: 1,
          xref: 'x',
          yref: 'paper',
          line: { color: 'rgba(34, 211, 238, 0.9)', width: 2, dash: 'dot' },
        },
      ],
    },
  }
}
