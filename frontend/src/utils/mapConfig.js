/** Kazakhstan-only mapbox view — keeps KZ filling most of the map panel */
export const KZ_MAPBOX = {
  style: 'carto-positron',
  center: { lat: 48.2, lon: 67.0 },
  zoom: 4.55,
  bounds: { west: 46.5, east: 87.5, south: 40.5, north: 55.2 },
}

export const KZ_MAP_LAYOUT = {
  mapbox: {
    style: KZ_MAPBOX.style,
    center: KZ_MAPBOX.center,
    zoom: KZ_MAPBOX.zoom,
    bearing: 0,
    pitch: 0,
  },
  margin: { l: 0, r: 0, t: 0, b: 0 },
  dragmode: 'pan',
}

export const KZ_MAP_CONFIG = {
  responsive: true,
  displayModeBar: false,
  displaylogo: false,
  scrollZoom: false,
  doubleClick: false,
  modeBarButtonsToRemove: ['zoom2d', 'pan2d', 'select2d', 'lasso2d'],
}

export function regionStatsMap(regionStats) {
  const map = {}
  if (!Array.isArray(regionStats)) return map
  for (const row of regionStats) {
    if (row?.region) map[row.region] = row
  }
  return map
}
