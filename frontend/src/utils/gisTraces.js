/** Build Plotly scattermapbox traces from GeoJSON + monitoring data */

const STATUS_COLORS = {
  normal: '#22c55e',
  moderate: '#eab308',
  high: '#ef4444',
}

const BASIN_COLORS = {
  Ertis: '#2dd4bf',
  'Aralo-Syrdarya': '#38bdf8',
  'Balkash-Alakol': '#a78bfa',
  'Zhaiyk-Kaspian': '#fbbf24',
  'Tobyl-Torgay': '#94a3b8',
  'Shu-Talas': '#34d399',
  Esil: '#60a5fa',
  'Nura-Sarysu': '#f472b6',
  Global_Reference: '#64748b',
}

export function riverTraces(riversGeojson, { visible = true } = {}) {
  if (!riversGeojson?.features?.length) return []
  return riversGeojson.features.map((feat) => {
    const coords = feat.geometry?.coordinates || []
    const props = feat.properties || {}
    return {
      type: 'scattermapbox',
      mode: 'lines',
      lat: coords.map((c) => c[1]),
      lon: coords.map((c) => c[0]),
      line: { color: 'rgba(56, 189, 248, 0.75)', width: 2.5 },
      name: props.name,
      customdata: [['river', props.id, props.name, props.basin]],
      hovertemplate: `<b>${props.name}</b><br>%{customdata[3]}<extra></extra>`,
      showlegend: false,
      visible,
    }
  })
}

export function lakeTraces(lakesGeojson, lakeStats = [], { visible = true } = {}) {
  if (!lakesGeojson?.features?.length) return []
  const statsById = Object.fromEntries((lakeStats || []).map((l) => [l.id, l]))
  return lakesGeojson.features.map((feat) => {
    const ring = feat.geometry?.coordinates?.[0] || []
    const props = feat.properties || {}
    const stats = statsById[props.id] || {}
    const wqi = stats.mean_wqi != null ? stats.mean_wqi : '—'
    return {
      type: 'scattermapbox',
      mode: 'lines',
      fill: 'toself',
      lat: ring.map((c) => c[1]),
      lon: ring.map((c) => c[0]),
      fillcolor: 'rgba(34, 211, 238, 0.22)',
      line: { color: 'rgba(34, 211, 238, 0.65)', width: 2 },
      name: props.name,
      customdata: [['lake', props.id, props.name, props.basin, wqi]],
      hovertemplate: `<b>${props.name}</b><br>WQI ${wqi}<extra></extra>`,
      showlegend: false,
      visible,
    }
  })
}

export function basinTraces(basinsGeojson, { visible = false, activeBasin = null } = {}) {
  if (!basinsGeojson?.features?.length) return []
  return basinsGeojson.features.map((feat) => {
    const ring = feat.geometry?.coordinates?.[0] || []
    const props = feat.properties || {}
    const isActive = activeBasin === props.id
    const color = BASIN_COLORS[props.id] || '#64748b'
    return {
      type: 'scattermapbox',
      mode: 'lines',
      fill: 'toself',
      lat: ring.map((c) => c[1]),
      lon: ring.map((c) => c[0]),
      fillcolor: isActive ? `${color}55` : `${color}22`,
      line: { color: isActive ? color : `${color}88`, width: isActive ? 2.5 : 1 },
      name: props.display_name || props.name,
      customdata: [['basin', props.id, props.display_name || props.name]],
      hovertemplate: `<b>${props.display_name || props.name}</b><extra></extra>`,
      showlegend: false,
      visible,
    }
  })
}

export function stationTraces(stations = [], { visible = true, pollutionMode = false } = {}) {
  if (!stations.length) return []
  return [{
    type: 'scattermapbox',
    mode: 'markers',
    lat: stations.map((s) => s.lat),
    lon: stations.map((s) => s.lon),
    marker: {
      size: stations.map((s) => (pollutionMode ? 10 + Math.min(s.max_ratio * 4, 18) : 11)),
      color: stations.map((s) => STATUS_COLORS[s.status] || STATUS_COLORS.normal),
      line: { width: 1.5, color: '#fff' },
      opacity: 0.95,
    },
    customdata: stations.map((s) => ['station', s.code, s.name, s.basin, s.status, s.mean_wqi]),
    hovertemplate:
      '<b>%{customdata[2]}</b><br>'
      + 'WQI %{customdata[5]:.1f}<br>'
      + '%{customdata[3]}<extra></extra>',
    name: 'stations',
    showlegend: false,
    visible,
  }]
}

export function hotspotTraces(hotspots = [], { visible = false } = {}) {
  if (!hotspots.length || !visible) return []
  return [{
    type: 'scattermapbox',
    mode: 'markers',
    lat: hotspots.map((h) => h.lat),
    lon: hotspots.map((h) => h.lon),
    marker: {
      size: hotspots.map((h) => 18 + Math.min(h.intensity * 6, 30)),
      color: hotspots.map((h) => (h.status === 'high' ? 'rgba(239,68,68,0.55)' : 'rgba(234,179,8,0.45)')),
      line: { width: 0 },
    },
    customdata: hotspots.map((h) => ['hotspot', h.code, h.name, h.intensity]),
    hovertemplate: '<b>%{customdata[2]}</b><br>Ratio %{customdata[3]:.2f}× MPC<extra></extra>',
    showlegend: false,
    visible: true,
  }]
}

export { BASIN_COLORS, STATUS_COLORS }
