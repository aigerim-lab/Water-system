import { useCallback, useState } from 'react'

export function useMapSelection() {
  const [selectedRegion, setSelectedRegion] = useState(null)
  const [hoverRegion, setHoverRegion] = useState(null)
  const [hoverStats, setHoverStats] = useState(null)
  const [selectedBasin, setSelectedBasin] = useState(null)
  const [geoSelection, setGeoSelection] = useState(null)

  const selectRegion = useCallback((region) => {
    setSelectedRegion(region || null)
    setGeoSelection(null)
  }, [])

  const selectBasin = useCallback((basinId) => {
    setSelectedBasin(basinId || null)
    if (basinId) {
      setGeoSelection({ type: 'basin', id: basinId, name: basinId })
    } else {
      setGeoSelection(null)
    }
  }, [])

  const selectGeo = useCallback((sel) => {
    setGeoSelection(sel)
    if (sel?.type === 'basin') setSelectedBasin(sel.id)
  }, [])

  const clearGeo = useCallback(() => {
    setGeoSelection(null)
  }, [])

  const setHover = useCallback((region, stats = null) => {
    setHoverRegion(region || null)
    setHoverStats(stats || null)
  }, [])

  return {
    selectedRegion,
    hoverRegion,
    hoverStats,
    selectedBasin,
    geoSelection,
    setHoverRegion: setHover,
    selectRegion,
    selectBasin,
    selectGeo,
    clearGeo,
  }
}
