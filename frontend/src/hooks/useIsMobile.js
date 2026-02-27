import { useState, useEffect } from 'react'

export function useIsMobile() {
  const [isMobile, setIsMobile] = useState(() => {
    return window.innerWidth < 768 || 'ontouchstart' in window
  })

  useEffect(() => {
    const mq = window.matchMedia('(max-width: 767px)')
    const handler = (e) => setIsMobile(e.matches)
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [])

  return isMobile
}
