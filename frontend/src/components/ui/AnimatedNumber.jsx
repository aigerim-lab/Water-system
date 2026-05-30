import React, { useEffect, useState } from 'react'

export function AnimatedNumber({ value, decimals = 0, duration = 1200 }) {
  const [display, setDisplay] = useState(0)
  const num = Number(value)
  const valid = Number.isFinite(num)

  useEffect(() => {
    if (!valid) return undefined
    const start = performance.now()
    const from = display
    const to = num
    let frame
    const tick = (now) => {
      const t = Math.min(1, (now - start) / duration)
      const eased = 1 - (1 - t) ** 3
      setDisplay(from + (to - from) * eased)
      if (t < 1) frame = requestAnimationFrame(tick)
    }
    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [num, valid, duration])

  if (!valid) return '—'
  return display.toFixed(decimals)
}
