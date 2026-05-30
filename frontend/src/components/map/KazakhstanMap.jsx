import React, { useCallback, useMemo } from 'react'
import { useLanguage } from '../../i18n/LanguageContext.jsx'
import { LazyPlot } from '../LazyPlot.jsx'
import { KZ_MAPBOX, KZ_MAP_CONFIG, KZ_MAP_LAYOUT, regionStatsMap } from '../../utils/mapConfig.js'
import {
  basinTraces,
  BASIN_COLORS,
  hotspotTraces,
  lakeTraces,
  riverTraces,
  stationTraces,
} from '../../utils/gisTraces.js'

const WQI_COLORS = [
  [0, '#059669'],
  [0.25, '#84cc16'],
  [0.5, '#eab308'],
  [0.75, '#f97316'],
  [1, '#dc2626'],
]

export function KazakhstanMap({
  figure,
  plotLayout,
  mapMode,
  gis,
  regionStats,
  hotspotRegions,
  selectedRegion,
  selectedBasin,
  onRegionSelect,
  onHoverRegion,
  onGeoSelect,
  height = 520,
}) {
  const { t } = useLanguage()
  const statsByRegion = useMemo(() => regionStatsMap(regionStats), [regionStats])
  const hotSet = useMemo(() => new Set(Array.isArray(hotspotRegions) ? hotspotRegions : []), [hotspotRegions])

  const hoverTemplate = useMemo(
    () => `<b>%{location}</b><br>${t('map.hoverWqi')}: %{z:.1f}<extra></extra>`,
    [t]
  )

  const choroplethTrace = useMemo(() => {
    if (!Array.isArray(figure?.data) || !figure.data.length) return null
    const trace = figure.data.find((tr) => tr?.type === 'choroplethmapbox')
    if (!trace) return null

    const locations = Array.isArray(trace.locations) ? trace.locations : []
    let zValues = Array.isArray(trace.z) ? [...trace.z] : []
    let colorscale = WQI_COLORS
    let marker = { line: { width: 0.5, color: 'rgba(255,255,255,0.25)' } }

    if (mapMode === 'hotspot') {
      colorscale = 'Reds'
      zValues = locations.map((loc) =>
        (hotSet.has(loc) ? statsByRegion[loc]?.mean_wqi ?? 0 : 0))
      marker.line.width = locations.map((loc) => (hotSet.has(loc) ? 2.5 : 0.4))
      marker.line.color = locations.map((loc) =>
        (hotSet.has(loc) ? 'rgba(248,113,113,0.95)' : 'rgba(255,255,255,0.12)'))
    } else if (mapMode === 'pollution') {
      colorscale = 'OrRd'
      zValues = locations.map((loc) => statsByRegion[loc]?.max_ratio ?? 0)
    } else if (mapMode === 'basins') {
      const basinIds = locations.map((loc) => statsByRegion[loc]?.basin || 'unknown')
      const uniq = [...new Set(basinIds)]
      zValues = basinIds.map((b) => uniq.indexOf(b))
      colorscale = uniq.map((b, i) => [i / Math.max(uniq.length - 1, 1), BASIN_COLORS[b] || '#64748b'])
    }

    if (selectedRegion) {
      marker.line.width = locations.map((loc) => {
        if (loc === selectedRegion) return 3
        return Array.isArray(marker.line.width) ? marker.line.width[locations.indexOf(loc)] : 0.5
      })
      marker.line.color = locations.map((loc, i) =>
        (loc === selectedRegion ? '#fff' : (Array.isArray(marker.line.color) ? marker.line.color[i] : 'rgba(255,255,255,0.2)')))
    }

    return {
      ...trace,
      z: zValues,
      colorscale,
      zauto: mapMode !== 'basins',
      marker,
      hovertemplate: hoverTemplate,
      showscale: mapMode !== 'basins',
      opacity: mapMode === 'basins' ? 0.35 : 0.75,
    }
  }, [figure, mapMode, hotSet, statsByRegion, selectedRegion, hoverTemplate])

  const overlayTraces = useMemo(() => {
    if (!gis) return []
    const showBasins = mapMode === 'basins'
    const showPollution = mapMode === 'pollution' || mapMode === 'hotspot'
    return [
      ...basinTraces(gis.basins, { visible: showBasins, activeBasin: selectedBasin }),
      ...lakeTraces(gis.lakes, gis.lake_stats, { visible: true }),
      ...riverTraces(gis.rivers, { visible: true }),
      ...stationTraces(gis.stations, { visible: true, pollutionMode: showPollution }),
      ...hotspotTraces(gis.hotspots, { visible: showPollution }),
    ]
  }, [gis, mapMode, selectedBasin])

  const data = useMemo(() => {
    if (!choroplethTrace) return null
    return [choroplethTrace, ...overlayTraces]
  }, [choroplethTrace, overlayTraces])

  const handleClick = useCallback(
    (ev) => {
      const pt = ev?.points?.[0]
      if (!pt) return

      const cd = pt.customdata
      if (Array.isArray(cd) && cd.length >= 2 && typeof cd[0] === 'string') {
        onGeoSelect?.({ type: cd[0], id: cd[1], name: cd[2], basin: cd[3] })
        return
      }

      const loc = pt.location
      if (!loc || !onRegionSelect) return
      if (selectedRegion === loc) onRegionSelect(null)
      else onRegionSelect(loc)
    },
    [onGeoSelect, onRegionSelect, selectedRegion]
  )

  const handleHover = useCallback(
    (ev) => {
      const pt = ev?.points?.[0]
      if (!pt) return
      if (pt.customdata?.[0] === 'station') {
        const code = pt.customdata[1]
        const station = gis?.stations?.find((s) => s.code === code)
        if (station) {
          onHoverRegion?.(station.region, {
            region: station.region,
            mean_wqi: station.mean_wqi,
            high_risk_pct: station.high_risk_pct,
            top_pollutant: station.top_pollutant,
            max_ratio: station.max_ratio,
            basin: station.basin,
          })
        }
        return
      }
      const loc = pt.location
      onHoverRegion?.(loc || null, loc ? statsByRegion[loc] : null)
    },
    [onHoverRegion, statsByRegion, gis]
  )

  const hStyle = height === '100%' ? { height: '100%', minHeight: '100%' } : { height }

  if (!data) {
    return (
      <div className="kz-map kz-map--empty chart-skeleton" style={hStyle}>
        <p className="empty-state">{t('empty.noMap')}</p>
      </div>
    )
  }

  return (
    <div className={`kz-map kz-map--mode-${mapMode}`} style={hStyle}>
      <LazyPlot
        data={data}
        layout={{
          ...(figure?.layout && typeof figure.layout === 'object' ? figure.layout : {}),
          ...KZ_MAP_LAYOUT,
          ...plotLayout,
          autosize: true,
          title: undefined,
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          mapbox: {
            ...KZ_MAP_LAYOUT.mapbox,
            ...(figure?.layout?.mapbox || {}),
            ...plotLayout?.mapbox,
            style: KZ_MAPBOX.style,
            center: KZ_MAP_LAYOUT.mapbox.center,
            zoom: KZ_MAP_LAYOUT.mapbox.zoom,
          },
        }}
        config={KZ_MAP_CONFIG}
        style={{ width: '100%', height: '100%' }}
        useResizeHandler
        onClick={handleClick}
        onHover={handleHover}
        onUnhover={() => onHoverRegion?.(null, null)}
      />
    </div>
  )
}
