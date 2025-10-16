'use client'

import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'
import { useTheme } from 'next-themes'

type VariantKey = 'default' | 'hover' | 'press' | 'button' | 'nav' | 'text' | 'disabled' | 'loading' | 'accent'

interface CursorContextValue {
  setVariant: (v: VariantKey) => void
  setText: (t: string) => void
  reset: () => void
  isEnabled: boolean
}

const CursorContext = createContext<CursorContextValue | null>(null)

export const useCursor = () => {
  const ctx = useContext(CursorContext)
  if (!ctx) throw new Error('useCursor must be used within <AnimatedCursorProvider />')
  return ctx
}




const lerp = (a: number, b: number, n: number) => {
  const diff = b - a
  return Math.abs(diff) < 0.01 ? b : a + diff * n
}

const SELECTORS: Record<VariantKey, string[]> = {
  default: [],
  hover: [
    'a:not([data-cursor="disabled"])',
    '.interactive',
    '.cursor-interactive',
    '[data-cursor="hover"]'
  ],
  button: [
    'button:not(:disabled)',
    '.btn-primary:not(:disabled)',
    '.btn-ghost:not(:disabled)',
    '[role="button"]:not([aria-disabled="true"])',
    '[data-cursor="button"]'
  ],
  nav: [
    '.nav-link',
    '[data-cursor="nav"]'
  ],
  press: [], 
  text: [
    'input:not(:disabled)',
    'textarea:not(:disabled)',
    '[contenteditable="true"]',
    '[data-cursor="text"]'
  ],
  disabled: [
    'button:disabled',
    '[aria-disabled="true"]',
    '[data-cursor="disabled"]'
  ],
  loading: [
    '[data-cursor="loading"]'
  ],
  accent: [
    '[data-cursor="accent"]'
  ]
}


interface VariantStyle {
  '--cursor-size'?: string
  '--cursor-color'?: string
  '--cursor-border'?: string
  '--cursor-scale'?: string
  '--cursor-blur'?: string
  '--cursor-backdrop'?: string
  '--cursor-mix'?: string
  '--cursor-ring-opacity'?: string
  '--cursor-dot-size'?: string
  '--cursor-glow'?: string
}


const getVariantStyles = (isDark: boolean): Record<VariantKey, VariantStyle> => ({
  default: {
    '--cursor-size': '42px',
    '--cursor-color': isDark ? '148 163 184' : '71 85 105',
    '--cursor-border': isDark 
      ? '2px solid rgba(148,163,184,0.4)' 
      : '2px solid rgba(71,85,105,0.3)',
    '--cursor-scale': '1',
    '--cursor-ring-opacity': isDark ? '0.8' : '0.6',
    '--cursor-dot-size': '6px',
    '--cursor-glow': isDark ? '0 0 20px rgba(148,163,184,0.3)' : '0 0 15px rgba(71,85,105,0.2)'
  },
  hover: {
    '--cursor-size': '56px',
    '--cursor-border': isDark 
      ? '2px solid rgba(59,130,246,0.7)' 
      : '2px solid rgba(59,130,246,0.6)',
    '--cursor-color': '59 130 246',
    '--cursor-ring-opacity': isDark ? '0.9' : '0.7',
    '--cursor-glow': isDark ? '0 0 30px rgba(59,130,246,0.4)' : '0 0 20px rgba(59,130,246,0.3)'
  },
  button: {
    '--cursor-size': '68px',
    '--cursor-border': isDark 
      ? '3px solid rgba(34,197,94,0.8)' 
      : '3px solid rgba(34,197,94,0.7)',
    '--cursor-color': '34 197 94',
    '--cursor-scale': '1.08',
    '--cursor-ring-opacity': isDark ? '0.95' : '0.8',
    '--cursor-dot-size': '8px',
    '--cursor-glow': isDark ? '0 0 35px rgba(34,197,94,0.5)' : '0 0 25px rgba(34,197,94,0.4)'
  },
  nav: {
    '--cursor-size': '58px',
    '--cursor-border': isDark 
      ? '2px solid rgba(96,165,250,0.8)' 
      : '2px solid rgba(96,165,250,0.6)',
    '--cursor-color': '96 165 250',
    '--cursor-ring-opacity': isDark ? '0.85' : '0.7',
    '--cursor-glow': isDark ? '0 0 28px rgba(96,165,250,0.4)' : '0 0 18px rgba(96,165,250,0.3)'
  },
  press: {
    '--cursor-scale': '0.88',
    '--cursor-glow': isDark ? '0 0 40px rgba(var(--cursor-color), 0.6)' : '0 0 30px rgba(var(--cursor-color), 0.5)'
  },
  text: {
    '--cursor-size': '4px',
    '--cursor-border': isDark 
      ? '1px solid rgba(168,85,247,0.9)' 
      : '1px solid rgba(168,85,247,0.8)',
    '--cursor-color': '168 85 247',
    '--cursor-dot-size': '0px',
    '--cursor-glow': isDark ? '0 0 15px rgba(168,85,247,0.6)' : '0 0 10px rgba(168,85,247,0.4)'
  },
  disabled: {
    '--cursor-size': '44px',
    '--cursor-border': isDark 
      ? '2px solid rgba(156,163,175,0.4)' 
      : '2px solid rgba(156,163,175,0.3)',
    '--cursor-color': '156 163 175',
    '--cursor-ring-opacity': isDark ? '0.4' : '0.3',
    '--cursor-glow': 'none'
  },
  loading: {
    '--cursor-size': '52px',
    '--cursor-border': isDark 
      ? '3px solid rgba(59,130,246,0.3)' 
      : '3px solid rgba(59,130,246,0.2)',
    '--cursor-color': '59 130 246',
    '--cursor-glow': isDark ? '0 0 25px rgba(59,130,246,0.4)' : '0 0 15px rgba(59,130,246,0.3)'
  },
  accent: {
    '--cursor-size': '76px',
    '--cursor-border': isDark 
      ? '3px solid rgba(236,72,153,0.9)' 
      : '3px solid rgba(236,72,153,0.8)',
    '--cursor-color': '236 72 153',
    '--cursor-scale': '1.15',
    '--cursor-ring-opacity': isDark ? '0.9' : '0.8',
    '--cursor-glow': isDark ? '0 0 40px rgba(236,72,153,0.6)' : '0 0 30px rgba(236,72,153,0.5)'
  }
})




interface AnimatedCursorProviderProps {
  children: React.ReactNode
  
  disableOnTouch?: boolean
}

export const AnimatedCursorProvider: React.FC<AnimatedCursorProviderProps> = ({ children }) => {
  const { resolvedTheme } = useTheme()
  const isDark = resolvedTheme === 'dark'
  const ringRef = useRef<HTMLDivElement>(null)
  const dotRef = useRef<HTMLDivElement>(null)
  const trailContainerRef = useRef<HTMLDivElement>(null)
  const variantRef = useRef<VariantKey>('default')
  const target = useRef({ x: typeof window !== 'undefined' ? window.innerWidth / 2 : 0, y: typeof window !== 'undefined' ? window.innerHeight / 2 : 0 })
  const pos = useRef({ x: target.current.x, y: target.current.y })
  const [isMounted, setIsMounted] = useState(false)
  const [cursorText, setCursorText] = useState('')
  const [isEnabled, setIsEnabled] = useState(true)
  const reducedMotion = useRef(false)
  const isPressed = useRef(false)
  const rafRef = useRef<number>()
  const trailRef = useRef<{x:number;y:number;el:HTMLSpanElement;life:number;isDark:boolean}[]>([])
  
  useEffect(() => {
    setIsMounted(true)
    reducedMotion.current = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const disabled = localStorage.getItem('nlpforge-disable-cursor') === 'true'
    if (disabled) setIsEnabled(false)
  }, [])

  const applyVariant = useCallback((v: VariantKey) => {
    const ring = ringRef.current
    const dot = dotRef.current
    if (!ring || !dot) return
    const styles = getVariantStyles(isDark)[v]
    Object.entries(styles).forEach(([k, val]) => {
      ring.style.setProperty(k, val || '')
      dot.style.setProperty(k, val || '')
    })
    ring.dataset.variant = v
    dot.dataset.variant = v
    ring.dataset.theme = isDark ? 'dark' : 'light'
    dot.dataset.theme = isDark ? 'dark' : 'light'
  }, [isDark])

  const setVariant = useCallback((v: VariantKey) => {
    variantRef.current = v
    applyVariant(v)
  }, [applyVariant])

  const reset = useCallback(() => {
    setVariant('default')
    setCursorText('')
  }, [setVariant])

  const spawnTrailPoint = useCallback((x: number, y: number) => {
    if (!trailContainerRef.current) return
    const el = document.createElement('span')
    el.className = 'cursor-trail-point'
    el.style.cssText = `left:${x}px;top:${y}px;opacity:0;transform:translate3d(-50%,-50%,0) scale(0.5)`
    el.dataset.theme = isDark ? 'dark' : 'light'
    const point = { x, y, el, life: 1, isDark }
    trailRef.current.push(point)
    trailContainerRef.current.appendChild(el)
    
    requestAnimationFrame(() => {
      el.style.opacity = (isDark ? '0.7' : '0.5')
      el.style.transform = 'translate3d(-50%, -50%, 0) scale(1)'
    })
  }, [isDark])

  const updateTrail = useCallback(() => {
    const dx = Math.abs(target.current.x - pos.current.x)
    const dy = Math.abs(target.current.y - pos.current.y)
    const distance = Math.sqrt(dx * dx + dy * dy)
    const threshold = 8
    
    if (distance > threshold) {
      spawnTrailPoint(pos.current.x, pos.current.y)
    }
    
    const maxTrailLength = isDark ? 8 : 6
    const fadeRate = 0.06
    
    for (let i = trailRef.current.length - 1; i >= 0; i--) {
      const p = trailRef.current[i]
      p.life -= fadeRate
      
      if (p.life <= 0 || trailRef.current.length > maxTrailLength) {
        p.el.remove()
        trailRef.current.splice(i, 1)
      } else {
        const easedLife = p.life * p.life
        const opacity = easedLife * (isDark ? 0.7 : 0.5)
        const scale = 0.6 + easedLife * 0.4
        
        p.el.style.opacity = opacity.toString()
        p.el.style.transform = `translate3d(-50%, -50%, 0) scale(${scale})`
      }
    }
  }, [isDark, spawnTrailPoint])

  const spawnTrailBurst = useCallback(() => {
    const burstCount = 4
    for (let i = 0; i < burstCount; i++) {
      setTimeout(() => {
        spawnTrailPoint(target.current.x, target.current.y)
      }, i * 20)
    }
  }, [spawnTrailPoint])

  
  useEffect(() => {
    if (!isMounted || !isEnabled || reducedMotion.current) return

    const handlePointerMove = (e: PointerEvent) => {
      target.current.x = e.clientX
      target.current.y = e.clientY
    }

    const resolveVariantFromEl = (el: HTMLElement | null): VariantKey | null => {
      if (!el) return null
      
      const explicit = el.getAttribute('data-cursor-variant') as VariantKey | null
      if (explicit && getVariantStyles(isDark)[explicit]) return explicit

      
      if (el.hasAttribute('data-cursor')) {
        const v = el.getAttribute('data-cursor') as VariantKey
        if (v && getVariantStyles(isDark)[v]) return v
      }

      
      if (el.matches(SELECTORS.button.join(','))) return 'button'
      if (el.matches(SELECTORS.nav.join(','))) return 'nav'
      if (el.matches(SELECTORS.text.join(','))) return 'text'
      if (el.matches(SELECTORS.disabled.join(','))) return 'disabled'
      if (el.matches(SELECTORS.hover.join(','))) return 'hover'
      
      
      if (el.closest('.dashboard-card, .metric-card, .highlight-tile')) return 'hover'
      if (el.closest('.glass-morphism, .glass-light, .glass-medium')) return 'hover'
      if (el.closest('.status-glow, .refresh-pulse')) return 'accent'
      if (el.closest('.group\\/card, .group')) return 'hover'
      
      return null
    }

    const handlePointerOver = (e: PointerEvent) => {
      const targetEl = e.target as HTMLElement
      const variant = resolveVariantFromEl(targetEl)
      if (variant) setVariant(variant)
      if (targetEl.hasAttribute('data-cursor-text')) {
        setCursorText(targetEl.getAttribute('data-cursor-text') || '')
      }
      if (targetEl.hasAttribute('data-cursor-color')) {
        ringRef.current?.style.setProperty('--cursor-color', targetEl.getAttribute('data-cursor-color') || '')
      }
      if (targetEl.hasAttribute('data-cursor-size')) {
        ringRef.current?.style.setProperty('--cursor-size', targetEl.getAttribute('data-cursor-size') || '')
      }
    }

    const handlePointerOut = (e: PointerEvent) => {
      const rel = (e.relatedTarget as HTMLElement) || null
      if (!rel || !(rel instanceof HTMLElement)) {
        reset()
        return
      }
      
      if (!resolveVariantFromEl(rel)) {
        reset()
      }
    }

    const handleDown = () => {
      isPressed.current = true
      setVariant('press')
      spawnTrailBurst()
    }
    const handleUp = () => {
      isPressed.current = false
      
      if (variantRef.current === 'press') setVariant('default')
    }

    window.addEventListener('pointermove', handlePointerMove)
    window.addEventListener('pointerover', handlePointerOver)
    window.addEventListener('pointerout', handlePointerOut)
    window.addEventListener('pointerdown', handleDown)
    window.addEventListener('pointerup', handleUp)

    return () => {
      window.removeEventListener('pointermove', handlePointerMove)
      window.removeEventListener('pointerover', handlePointerOver)
      window.removeEventListener('pointerout', handlePointerOut)
      window.removeEventListener('pointerdown', handleDown)
      window.removeEventListener('pointerup', handleUp)
    }
  }, [isMounted, isEnabled, reset, setVariant, isDark, spawnTrailBurst])

  
  useEffect(() => {
    if (!isMounted || !isEnabled || reducedMotion.current) return
    const ring = ringRef.current
    const dot = dotRef.current
    if (!ring || !dot) return

    const speed = 0.18
    const dotSpeed = 0.35
    let lastTime = performance.now()
    let frameCount = 0
    const targetFPS = 60
    const frameInterval = 1000 / targetFPS

    const frame = (currentTime: number) => {
      const deltaTime = currentTime - lastTime
      
      if (deltaTime >= frameInterval) {
        lastTime = currentTime - (deltaTime % frameInterval)
        frameCount++

        const adjustedSpeed = speed * (deltaTime / 16.67)
        const adjustedDotSpeed = dotSpeed * (deltaTime / 16.67)
        
        pos.current.x = lerp(pos.current.x, target.current.x, adjustedSpeed)
        pos.current.y = lerp(pos.current.y, target.current.y, adjustedSpeed)
        const dotX = lerp(pos.current.x, target.current.x, adjustedDotSpeed)
        const dotY = lerp(pos.current.y, target.current.y, adjustedDotSpeed)

        ring.style.transform = `translate3d(${pos.current.x}px, ${pos.current.y}px, 0)`
        dot.style.transform = `translate3d(${dotX}px, ${dotY}px, 0)`

        if (frameCount % 2 === 0) {
          updateTrail()
        }
      }
      
      rafRef.current = requestAnimationFrame(frame)
    }
    rafRef.current = requestAnimationFrame(frame)
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
    }
  }, [isMounted, isEnabled, isDark, updateTrail])

  
  useEffect(() => {
    if (isMounted) applyVariant('default')
  }, [isMounted, applyVariant])

  
  useEffect(() => {
    if (!isMounted) return
    if (!isEnabled || reducedMotion.current) return
    document.documentElement.classList.add('custom-cursor-active')
    return () => document.documentElement.classList.remove('custom-cursor-active')
  }, [isMounted, isEnabled])

  if (!isMounted || !isEnabled || reducedMotion.current || typeof window === 'undefined') {
    return <CursorContext.Provider value={{ setVariant, setText: setCursorText, reset, isEnabled: false }}>{children}</CursorContext.Provider>
  }

  return (
    <CursorContext.Provider value={{ setVariant, setText: setCursorText, reset, isEnabled }}>
      {children}
      <div id="animated-cursor-root" aria-hidden="true">
        <div ref={ringRef} className="animated-cursor-ring" />
        <div ref={dotRef} className="animated-cursor-dot" />
        <div ref={trailContainerRef} className="animated-cursor-trail" />
        {cursorText && (
          <div 
            className="animated-cursor-label" 
            data-variant={variantRef.current}
            data-theme={isDark ? 'dark' : 'light'}
          >
            {cursorText}
          </div>
        )}
      </div>
    </CursorContext.Provider>
  )
}


export const AnimatedCursor = AnimatedCursorProvider
