'use client'

import { useCallback, useEffect } from 'react'

export type CursorVariant = 'default' | 'hover' | 'click' | 'text' | 'disabled' | 'loading'

export function useCursor() {
  const setCursorVariant = useCallback((variant: CursorVariant) => {
    document.body.setAttribute('data-cursor-variant', variant)
    
    
    window.dispatchEvent(new CustomEvent('cursor-variant-change', {
      detail: { variant }
    }))
  }, [])

  const setCursorText = useCallback((text: string) => {
    document.body.setAttribute('data-cursor-text', text)
    
    window.dispatchEvent(new CustomEvent('cursor-text-change', {
      detail: { text }
    }))
  }, [])

  const resetCursor = useCallback(() => {
    setCursorVariant('default')
    document.body.removeAttribute('data-cursor-text')
  }, [setCursorVariant])

  
  useEffect(() => {
    return () => {
      resetCursor()
    }
  }, [resetCursor])

  return {
    setCursorVariant,
    setCursorText,
    resetCursor
  }
}


export function useCursorHover(variant: CursorVariant = 'hover') {
  const { setCursorVariant, resetCursor } = useCursor()

  const onMouseEnter = useCallback(() => {
    setCursorVariant(variant)
  }, [setCursorVariant, variant])

  const onMouseLeave = useCallback(() => {
    resetCursor()
  }, [resetCursor])

  return {
    onMouseEnter,
    onMouseLeave
  }
}


export function useCursorLoading(isLoading: boolean) {
  const { setCursorVariant, resetCursor } = useCursor()

  useEffect(() => {
    if (isLoading) {
      setCursorVariant('loading')
    } else {
      resetCursor()
    }
  }, [isLoading, setCursorVariant, resetCursor])
}
