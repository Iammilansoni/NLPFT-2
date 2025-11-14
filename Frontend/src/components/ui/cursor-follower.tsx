'use client'











import { useEffect, useRef, useState, useCallback } from 'react'

interface CursorPosition {
  x: number
  y: number
}

interface CursorFollowerProps {
  className?: string
}

export function CursorFollower({ className = '' }: CursorFollowerProps) {
  const cursorRef = useRef<HTMLDivElement>(null)
  const cursorDotRef = useRef<HTMLDivElement>(null)
  const [mousePosition, setMousePosition] = useState<CursorPosition>({ x: -100, y: -100 })
  const [isVisible, setIsVisible] = useState(false)
  const [isHovering, setIsHovering] = useState(false)
  const [isClicking, setIsClicking] = useState(false)
  const [cursorVariant, setCursorVariant] = useState<'default' | 'hover' | 'click' | 'text' | 'disabled' | 'loading' | 'button' | 'button-click' | 'nav-click'>('default')
  const [cursorText, setCursorText] = useState('')
  const [isOverButton, setIsOverButton] = useState(false)
  const [isOverNavLink, setIsOverNavLink] = useState(false)
  const mouseTrail = useRef<CursorPosition[]>([])

  
  const isTouchDevice = useCallback(() => {
    return 'ontouchstart' in window || 
           navigator.maxTouchPoints > 0 ||
           window.innerWidth < 768 
  }, [])

  
  useEffect(() => {
    if (isTouchDevice()) return

    let animationFrame: number

    const handleMouseMove = (e: MouseEvent) => {
      cancelAnimationFrame(animationFrame)
      
      animationFrame = requestAnimationFrame(() => {
        const newPosition = { x: e.clientX, y: e.clientY }
        setMousePosition(newPosition)
        
        
        mouseTrail.current.push(newPosition)
        if (mouseTrail.current.length > 10) {
          mouseTrail.current.shift()
        }
        
        if (!isVisible) {
          setIsVisible(true)
        }
      })
    }

    const handleMouseLeave = () => {
      setIsVisible(false)
      mouseTrail.current = []
      setIsOverButton(false)
    }

    const handleMouseEnter = (e: MouseEvent) => {
      
      setMousePosition({ x: e.clientX, y: e.clientY })
      setIsVisible(true)
    }

    
    const handleMouseDown = (e: MouseEvent) => {
      
      setMousePosition({ x: e.clientX, y: e.clientY })
      setIsClicking(true)
      
      
      const target = e.target as HTMLElement
      const isButton = target.closest('button, .btn-primary, .btn-secondary, .btn-outline, .btn-ghost, .button, [role="button"], .cta-button, .action-button, .submit-button')
      const isNavLink = target.closest('a, .nav-link, .menu-item, [data-cursor="nav"]')
      
      if (isButton) {
        setCursorVariant('button-click')
      } else if (isNavLink) {
        setCursorVariant('nav-click')
      } else {
        setCursorVariant('click')
      }
    }

    const handleMouseUp = (e: MouseEvent) => {
      
      setMousePosition({ x: e.clientX, y: e.clientY })
      setIsClicking(false)
      if (isOverButton) {
        setCursorVariant('button')
      } else if (isHovering) {
        setCursorVariant('hover')
      } else {
        setCursorVariant('default')
      }
    }

    
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseleave', handleMouseLeave)
    document.addEventListener('mouseenter', handleMouseEnter)
    document.addEventListener('mousedown', handleMouseDown)
    document.addEventListener('mouseup', handleMouseUp)

    return () => {
      cancelAnimationFrame(animationFrame)
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseleave', handleMouseLeave)
      document.removeEventListener('mouseenter', handleMouseEnter)
      document.removeEventListener('mousedown', handleMouseDown)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isVisible, isHovering, isOverButton, isTouchDevice])

  
  useEffect(() => {
    if (isTouchDevice()) return

    const handleCursorVariantChange = (e: CustomEvent) => {
      const { variant } = e.detail
      setCursorVariant(variant)
    }

    const handleCursorTextChange = (e: CustomEvent) => {
      const { text } = e.detail
      setCursorText(text)
    }

    window.addEventListener('cursor-variant-change', handleCursorVariantChange as EventListener)
    window.addEventListener('cursor-text-change', handleCursorTextChange as EventListener)

    return () => {
      window.removeEventListener('cursor-variant-change', handleCursorVariantChange as EventListener)
      window.removeEventListener('cursor-text-change', handleCursorTextChange as EventListener)
    }
  }, [isTouchDevice])

  
  useEffect(() => {
    if (isTouchDevice()) return

    const handleButtonHover = () => {
      setIsOverButton(true)
      setIsOverNavLink(false)
      setIsHovering(true)
      if (!isClicking) {
        setCursorVariant('button')
      }
      
      
      if (navigator.vibrate) {
        navigator.vibrate(10)
      }
    }

    const handleButtonLeave = () => {
      setIsOverButton(false)
      setIsHovering(false)
      if (!isClicking) {
        setCursorVariant('default')
      }
    }

    const handleNavHover = () => {
      setIsOverNavLink(true)
      setIsOverButton(false)
      setIsHovering(true)
      if (!isClicking) {
        setCursorVariant('hover')
      }
    }

    const handleNavLeave = () => {
      setIsOverNavLink(false)
      setIsHovering(false)
      if (!isClicking) {
        setCursorVariant('default')
      }
    }

    const handleElementHover = () => {
      setIsHovering(true)
      if (!isClicking && !isOverButton && !isOverNavLink) {
        setCursorVariant('hover')
      }
    }

    const handleElementLeave = () => {
      setIsHovering(false)
      if (!isClicking && !isOverButton && !isOverNavLink) {
        setCursorVariant('default')
      }
    }

    const handleTextHover = () => {
      setCursorVariant('text')
    }

    const handleDisabledHover = () => {
      setCursorVariant('disabled')
    }

    
    const buttonSelectors = [
      'button:not(:disabled)',
      '.btn-primary:not(:disabled)',
      '.btn-secondary:not(:disabled)',
      '.btn-outline:not(:disabled)',
      '.btn-ghost:not(:disabled)',
      '.button:not(:disabled)',
      '[role="button"]:not([aria-disabled="true"])',
      '.cta-button',
      '.action-button',
      '.submit-button',
      '[data-cursor="button"]'
    ]

    
    const interactiveSelectors = [
      '.interactive',
      '.card[data-clickable]',
      '.cursor-interactive',
      '[data-cursor="hover"]',
      '.tab-button',
      '.menu-item'
    ]

    
    const navSelectors = [
      'a:not(.btn-primary):not(.btn-secondary):not(.button)',
      '.nav-link',
      '.navigation a',
      '.menu a',
      '[data-cursor="nav"]'
    ]

    
    const textSelectors = [
      'input[type="text"]:not(:disabled)',
      'input[type="email"]:not(:disabled)',
      'input[type="password"]:not(:disabled)',
      'input[type="search"]:not(:disabled)',
      'textarea:not(:disabled)',
      '[contenteditable]:not([contenteditable="false"])',
      '[data-cursor="text"]'
    ]

    
    const disabledSelectors = [
      'button:disabled',
      '[disabled]',
      '.disabled',
      '[aria-disabled="true"]',
      '[data-cursor="disabled"]'
    ]

    
    const addListeners = () => {
      const buttonElements = document.querySelectorAll(buttonSelectors.join(', '))
      const navElements = document.querySelectorAll(navSelectors.join(', '))
      const interactiveElements = document.querySelectorAll(interactiveSelectors.join(', '))
      const textElements = document.querySelectorAll(textSelectors.join(', '))
      const disabledElements = document.querySelectorAll(disabledSelectors.join(', '))

      
      buttonElements.forEach(element => {
        element.addEventListener('mouseenter', handleButtonHover)
        element.addEventListener('mouseleave', handleButtonLeave)
      })

      
      navElements.forEach(element => {
        element.addEventListener('mouseenter', handleNavHover)
        element.addEventListener('mouseleave', handleNavLeave)
      })

      interactiveElements.forEach(element => {
        element.addEventListener('mouseenter', handleElementHover)
        element.addEventListener('mouseleave', handleElementLeave)
      })

      textElements.forEach(element => {
        element.addEventListener('mouseenter', handleTextHover)
        element.addEventListener('mouseleave', handleElementLeave)
      })

      disabledElements.forEach(element => {
        element.addEventListener('mouseenter', handleDisabledHover)
        element.addEventListener('mouseleave', handleElementLeave)
      })
    }

    
    addListeners()

    
    const observer = new MutationObserver(addListeners)
    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['disabled', 'aria-disabled', 'data-cursor']
    })

    return () => {
      observer.disconnect()
    }
  }, [isClicking, isOverButton, isOverNavLink, isTouchDevice])

  
  useEffect(() => {
    if (isTouchDevice()) return

    
    const hasValidPosition = mousePosition.x > -50 && mousePosition.y > -50

    if (cursorRef.current && hasValidPosition) {
      const cursor = cursorRef.current
      cursor.style.transform = `translate3d(${mousePosition.x}px, ${mousePosition.y}px, 0)`
    }

    if (cursorDotRef.current && hasValidPosition) {
      const dot = cursorDotRef.current
      
      requestAnimationFrame(() => {
        dot.style.transform = `translate3d(${mousePosition.x}px, ${mousePosition.y}px, 0)`
      })
    }
  }, [mousePosition, isTouchDevice])

  
  useEffect(() => {
    if (isTouchDevice()) return

    if (isVisible) {
      document.body.style.cursor = 'none'
      
      const style = document.createElement('style')
      style.textContent = `
        *, *::before, *::after {
          cursor: none !important;
        }
      `
      document.head.appendChild(style)
      
      return () => {
        document.head.removeChild(style)
        document.body.style.cursor = 'auto'
      }
    } else {
      document.body.style.cursor = 'auto'
    }
  }, [isVisible, isTouchDevice])

  
  if (isTouchDevice()) {
    return null
  }

  const getCursorStyles = () => {
    const baseStyles = {
      position: 'fixed' as const,
      top: 0,
      left: 0,
      pointerEvents: 'none' as const,
      zIndex: 9999,
      opacity: isVisible ? 1 : 0,
      transition: 'opacity 0.3s ease, width 0.15s ease, height 0.15s ease, border-color 0.15s ease, background-color 0.15s ease, box-shadow 0.15s ease',
      transform: 'translate3d(-50%, -50%, 0)',
      mixBlendMode: 'difference' as const
    }

    switch (cursorVariant) {
      case 'button-click':
        return {
          ...baseStyles,
          width: '120px',
          height: '120px',
          border: '4px solid rgba(34, 197, 94, 1)',
          borderRadius: '50%',
          background: 'rgba(34, 197, 94, 0.3)',
          boxShadow: '0 0 40px rgba(34, 197, 94, 0.8), inset 0 0 30px rgba(34, 197, 94, 0.4)',
          animation: 'buttonClickExpand 0.4s ease-out forwards'
        }
      case 'nav-click':
        return {
          ...baseStyles,
          width: '100px',
          height: '100px',
          border: '3px solid rgba(59, 130, 246, 1)',
          borderRadius: '50%',
          background: 'rgba(59, 130, 246, 0.25)',
          boxShadow: '0 0 35px rgba(59, 130, 246, 0.7), inset 0 0 25px rgba(59, 130, 246, 0.3)',
          animation: 'navClickExpand 0.3s ease-out forwards'
        }
      case 'button':
        return {
          ...baseStyles,
          width: '70px',
          height: '70px',
          border: '3px solid rgba(34, 197, 94, 0.9)',
          borderRadius: '50%',
          background: 'rgba(34, 197, 94, 0.15)',
          boxShadow: '0 0 20px rgba(34, 197, 94, 0.4), inset 0 0 20px rgba(34, 197, 94, 0.1)',
          animation: 'buttonPulse 1.5s ease-in-out infinite'
        }
      case 'hover':
        return {
          ...baseStyles,
          width: '60px',
          height: '60px',
          border: '2px solid rgba(59, 130, 246, 0.8)',
          borderRadius: '50%',
          background: 'rgba(59, 130, 246, 0.1)',
          boxShadow: '0 0 15px rgba(59, 130, 246, 0.3)'
        }
      case 'click':
        return {
          ...baseStyles,
          width: '30px',
          height: '30px',
          border: '2px solid rgba(239, 68, 68, 0.9)',
          borderRadius: '50%',
          background: 'rgba(239, 68, 68, 0.2)',
          boxShadow: '0 0 15px rgba(239, 68, 68, 0.5)'
        }
      case 'text':
        return {
          ...baseStyles,
          width: '2px',
          height: '24px',
          border: '1px solid rgba(168, 85, 247, 0.8)',
          borderRadius: '2px',
          background: 'rgba(168, 85, 247, 0.3)',
          animation: 'textBlink 1s ease-in-out infinite'
        }
      case 'disabled':
        return {
          ...baseStyles,
          width: '35px',
          height: '35px',
          border: '2px solid rgba(156, 163, 175, 0.6)',
          borderRadius: '50%',
          background: 'rgba(156, 163, 175, 0.1)',
          opacity: isVisible ? 0.5 : 0
        }
      case 'loading':
        return {
          ...baseStyles,
          width: '50px',
          height: '50px',
          border: '3px solid rgba(59, 130, 246, 0.3)',
          borderTop: '3px solid rgba(59, 130, 246, 0.9)',
          borderRadius: '50%',
          background: 'transparent',
          animation: 'spin 1s linear infinite'
        }
      default:
        return {
          ...baseStyles,
          width: '40px',
          height: '40px',
          border: '2px solid rgba(255, 255, 255, 0.7)',
          borderRadius: '50%',
          background: 'transparent'
        }
    }
  }

  const getDotStyles = () => {
    const baseStyles = {
      position: 'fixed' as const,
      top: 0,
      left: 0,
      width: '6px',
      height: '6px',
      borderRadius: '50%',
      pointerEvents: 'none' as const,
      zIndex: 10000,
      opacity: isVisible && cursorVariant !== 'text' && cursorVariant !== 'loading' ? 1 : 0,
      transition: 'opacity 0.3s ease, transform 0.15s ease, background-color 0.15s ease, scale 0.15s ease',
      transform: `translate3d(-50%, -50%, 0) scale(${
        cursorVariant === 'button-click' ? '3' : 
        cursorVariant === 'nav-click' ? '2.5' : 
        cursorVariant === 'click' ? '1.5' : 
        cursorVariant === 'button' ? '1.8' : '1'
      })`,
      mixBlendMode: 'difference' as const
    }

    switch (cursorVariant) {
      case 'button-click':
        return { 
          ...baseStyles, 
          backgroundColor: 'rgba(34, 197, 94, 1)',
          boxShadow: '0 0 20px rgba(34, 197, 94, 1)',
          width: '10px',
          height: '10px'
        }
      case 'nav-click':
        return { 
          ...baseStyles, 
          backgroundColor: 'rgba(59, 130, 246, 1)',
          boxShadow: '0 0 15px rgba(59, 130, 246, 1)',
          width: '8px',
          height: '8px'
        }
      case 'button':
        return { 
          ...baseStyles, 
          backgroundColor: 'rgba(34, 197, 94, 1)',
          boxShadow: '0 0 10px rgba(34, 197, 94, 0.8)'
        }
      case 'hover':
        return { ...baseStyles, backgroundColor: 'rgba(59, 130, 246, 1)' }
      case 'click':
        return { 
          ...baseStyles, 
          backgroundColor: 'rgba(239, 68, 68, 1)',
          boxShadow: '0 0 8px rgba(239, 68, 68, 0.8)'
        }
      case 'disabled':
        return { ...baseStyles, backgroundColor: 'rgba(156, 163, 175, 0.8)' }
      default:
        return { ...baseStyles, backgroundColor: 'rgba(255, 255, 255, 0.9)' }
    }
  }

  return (
    <>
      <div
        ref={cursorRef}
        className={`cursor-ring ${className} ${cursorVariant === 'button' ? 'cursor-button' : ''} ${cursorVariant === 'hover' ? 'cursor-hover' : ''} ${cursorVariant === 'disabled' ? 'cursor-disabled' : ''}`}
        style={getCursorStyles()}
      />

      <div
        ref={cursorDotRef}
        className="cursor-dot"
        style={getDotStyles()}
      />

      {cursorText && (
        <div
          className="cursor-text"
          style={{
            position: 'fixed',
            top: mousePosition.y - 40,
            left: mousePosition.x + 20,
            background: 'rgba(0, 0, 0, 0.8)',
            color: 'white',
            padding: '4px 8px',
            borderRadius: '4px',
            fontSize: '12px',
            fontWeight: '500',
            pointerEvents: 'none',
            zIndex: 10001,
            opacity: isVisible ? 1 : 0,
            transition: 'opacity 0.3s ease',
            whiteSpace: 'nowrap'
          }}
        >
          {cursorText}
        </div>
      )}

      {isClicking && (
        <div
          className="cursor-ripple"
          style={{
            position: 'fixed',
            top: mousePosition.y,
            left: mousePosition.x,
            width: '0',
            height: '0',
            border: `2px solid rgba(${
              cursorVariant === 'button-click' ? '34, 197, 94' : 
              cursorVariant === 'nav-click' ? '59, 130, 246' : 
              '239, 68, 68'
            }, 0.8)`,
            borderRadius: '50%',
            pointerEvents: 'none',
            zIndex: 9998,
            transform: 'translate3d(-50%, -50%, 0)',
            animation: `${
              cursorVariant === 'button-click' ? 'buttonRipple' : 
              cursorVariant === 'nav-click' ? 'navRipple' : 
              'cursorRipple'
            } 0.6s ease-out forwards`
          }}
        />
      )}

      <style jsx>{`
        @keyframes spin {
          0% { transform: translate3d(-50%, -50%, 0) rotate(0deg); }
          100% { transform: translate3d(-50%, -50%, 0) rotate(360deg); }
        }
        
        @keyframes buttonPulse {
          0%, 100% { 
            box-shadow: 0 0 20px rgba(34, 197, 94, 0.4), inset 0 0 20px rgba(34, 197, 94, 0.1);
            border-color: rgba(34, 197, 94, 0.9);
          }
          50% { 
            box-shadow: 0 0 30px rgba(34, 197, 94, 0.6), inset 0 0 25px rgba(34, 197, 94, 0.2);
            border-color: rgba(34, 197, 94, 1);
          }
        }
        
        @keyframes buttonClickExpand {
          0% {
            width: 70px;
            height: 70px;
            opacity: 1;
            background: rgba(34, 197, 94, 0.15);
          }
          50% {
            width: 120px;
            height: 120px;
            opacity: 0.9;
            background: rgba(34, 197, 94, 0.3);
          }
          100% {
            width: 120px;
            height: 120px;
            opacity: 1;
            background: rgba(34, 197, 94, 0.3);
          }
        }
        
        @keyframes navClickExpand {
          0% {
            width: 60px;
            height: 60px;
            opacity: 1;
            background: rgba(59, 130, 246, 0.1);
          }
          50% {
            width: 100px;
            height: 100px;
            opacity: 0.9;
            background: rgba(59, 130, 246, 0.25);
          }
          100% {
            width: 100px;
            height: 100px;
            opacity: 1;
            background: rgba(59, 130, 246, 0.25);
          }
        }
        
        @keyframes textBlink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0.3; }
        }
        
        @keyframes cursorRipple {
          0% {
            width: 0;
            height: 0;
            opacity: 1;
          }
          100% {
            width: 60px;
            height: 60px;
            opacity: 0;
          }
        }
        
        @keyframes buttonRipple {
          0% {
            width: 0;
            height: 0;
            opacity: 1;
          }
          100% {
            width: 120px;
            height: 120px;
            opacity: 0;
          }
        }
        
        @keyframes navRipple {
          0% {
            width: 0;
            height: 0;
            opacity: 1;
          }
          100% {
            width: 100px;
            height: 100px;
            opacity: 0;
          }
        }
      `}</style>
    </>
  )
}
