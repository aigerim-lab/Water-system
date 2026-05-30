/** Normalize unknown API / state values before spread, map, or Math.min/max. */
export function asArray(value) {
  if (Array.isArray(value)) return value
  if (value == null) return []
  if (typeof value === 'object') return Object.values(value)
  return [value]
}

export function asNumberArray(value) {
  return asArray(value).map(Number).filter(Number.isFinite)
}

export function safeYears(value) {
  return asNumberArray(value)
}

export function safeRegions(value) {
  return asArray(value).map(String).filter(Boolean)
}

export function safePollutants(value) {
  return asArray(value).map(String).filter(Boolean)
}

export function safeBasins(value) {
  return asArray(value).map(String).filter(Boolean)
}

export function safeSources(value) {
  return asArray(value).map(String).filter(Boolean)
}

export function minOf(value) {
  const arr = asNumberArray(value)
  return arr.length ? Math.min(...arr) : null
}

export function maxOf(value) {
  const arr = asNumberArray(value)
  return arr.length ? Math.max(...arr) : null
}

export function normalizeFilterOptions(opts) {
  if (!opts || typeof opts !== 'object') {
    return { sources: [], regions: [], years: [], pollutants: [], basins: [] }
  }
  return {
    ...opts,
    sources: safeSources(opts.sources),
    regions: safeRegions(opts.regions),
    basins: safeBasins(opts.basins),
    years: safeYears(opts.years),
    pollutants: safePollutants(opts.pollutants),
  }
}

export function normalizeFilters(filters, fallbackOptions = {}) {
  const fb = normalizeFilterOptions(fallbackOptions)
  const f = filters && typeof filters === 'object' ? filters : {}
  return {
    sources: safeSources(f.sources).length ? safeSources(f.sources) : fb.sources,
    regions: safeRegions(f.regions).length ? safeRegions(f.regions) : fb.regions,
    years: safeYears(f.years).length ? safeYears(f.years) : fb.years,
    pollutants: safePollutants(f.pollutants).length ? safePollutants(f.pollutants) : fb.pollutants,
    basins: safeBasins(f.basins).length ? safeBasins(f.basins) : fb.basins,
  }
}

export function buildFilterPayload(filters, lang) {
  const f = normalizeFilters(filters)
  return {
    sources: f.sources.length ? f.sources : undefined,
    regions: f.regions.length ? f.regions : undefined,
    years: f.years.length ? f.years : undefined,
    pollutants: f.pollutants.length ? f.pollutants : undefined,
    basins: f.basins.length ? f.basins : undefined,
    lang,
  }
}
