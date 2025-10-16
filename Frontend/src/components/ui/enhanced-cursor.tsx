'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { motion, useMotionValue, useSpring } from 'framer-motion';

interface EnhancedCursorProps {
  children: React.ReactNode;
}


export function EnhancedCursor({ children }: EnhancedCursorProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [isHovering, setIsHovering] = useState(false);
  const rafRef = useRef<number | null>(null);

  
  const cursorX = useMotionValue(0);
  const cursorY = useMotionValue(0);

  
  const springConfig = { damping: 25, stiffness: 300, mass: 0.5 };
  const cursorXSpring = useSpring(cursorX, springConfig);
  const cursorYSpring = useSpring(cursorY, springConfig);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current);
    }

    rafRef.current = requestAnimationFrame(() => {
      cursorX.set(e.clientX);
      cursorY.set(e.clientY);

      
      const target = e.target as HTMLElement;
      const isInteractive = 
        target.tagName === 'A' ||
        target.tagName === 'BUTTON' ||
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.onclick !== null ||
        target.classList.contains('cursor-pointer') ||
        target.getAttribute('role') === 'button';

      setIsHovering(isInteractive);
    });
  }, [cursorX, cursorY]);

  const handleMouseEnter = useCallback(() => {
    setIsVisible(true);
  }, []);

  const handleMouseLeave = useCallback(() => {
    setIsVisible(false);
  }, []);

  useEffect(() => {
    
    const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    if (isTouchDevice) {
      return;
    }

    
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (mediaQuery.matches) {
      return;
    }

    
    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    document.body.addEventListener('mouseenter', handleMouseEnter);
    document.body.addEventListener('mouseleave', handleMouseLeave);

    
    document.body.style.cursor = 'none';
    document.querySelectorAll('a, button, input, textarea, [role="button"]').forEach((el) => {
      (el as HTMLElement).style.cursor = 'none';
    });

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      document.body.removeEventListener('mouseenter', handleMouseEnter);
      document.body.removeEventListener('mouseleave', handleMouseLeave);
      
      
      document.body.style.cursor = '';
      document.querySelectorAll('a, button, input, textarea, [role="button"]').forEach((el) => {
        (el as HTMLElement).style.cursor = '';
      });

      if (rafRef.current !== null) {
        cancelAnimationFrame(rafRef.current);
      }
    };
  }, [handleMouseMove, handleMouseEnter, handleMouseLeave]);

  const shouldShowCursor = isVisible && typeof window !== 'undefined' && !('ontouchstart' in window);

  return (
    <>
      {children}
      {shouldShowCursor && (
        <div className="pointer-events-none fixed inset-0 z-cursor" aria-hidden="true">
          <motion.div
            className="absolute w-1.5 h-1.5 bg-primary rounded-full mix-blend-difference"
            style={{
              left: cursorXSpring,
              top: cursorYSpring,
              x: '-50%',
              y: '-50%',
            }}
            animate={{
              scale: isHovering ? 1.5 : 1,
            }}
            transition={{
              type: 'spring',
              damping: 20,
              stiffness: 400,
            }}
          />

          <motion.div
            className="absolute w-8 h-8 border-2 border-primary/50 rounded-full mix-blend-difference"
            style={{
              left: cursorXSpring,
              top: cursorYSpring,
              x: '-50%',
              y: '-50%',
            }}
            animate={{
              scale: isHovering ? 1.5 : 1,
              opacity: isHovering ? 1 : 0.6,
            }}
            transition={{
              type: 'spring',
              damping: 25,
              stiffness: 300,
            }}
          />
        </div>
      )}
    </>
  );
}
