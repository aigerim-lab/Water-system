import React from 'react'
import { useSectionReveal } from '../../hooks/useSectionReveal.js'

export function StorySection({
  id,
  chapter,
  eyebrow,
  title,
  lead,
  insight,
  variant = 'default',
  children,
}) {
  const { ref, className } = useSectionReveal()

  return (
    <section
      id={id}
      ref={ref}
      className={`story-section story-section--${variant} ${className}`}
    >
      {chapter != null && <span className="story-section__chapter">{String(chapter).padStart(2, '0')}</span>}
      {eyebrow && <p className="story-section__eyebrow">{eyebrow}</p>}
      {title && <h2 className="story-section__title">{title}</h2>}
      {lead && <p className="story-section__lead">{lead}</p>}
      {insight && <blockquote className="story-section__insight">{insight}</blockquote>}
      {children && <div className="story-section__body">{children}</div>}
    </section>
  )
}
