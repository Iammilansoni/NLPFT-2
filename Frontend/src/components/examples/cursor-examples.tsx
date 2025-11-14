"use client";



import { useState } from 'react'
import { useCursor, useCursorHover, useCursorLoading } from '@/hooks/use-cursor'
import { Button } from '@/components/ui/button'


export function ExampleButton() {
  const cursorHover = useCursorHover('hover')
  
  return (
    <Button 
      className="btn-primary cursor-interactive"
      {...cursorHover}
    >
      Hover me!
    </Button>
  )
}


export function ExampleCard() {
  const { setCursorVariant, setCursorText, resetCursor } = useCursor()
  
  return (
    <div 
      className="card cursor-interactive"
      onMouseEnter={() => {
        setCursorVariant('hover')
        setCursorText('Click to view details')
      }}
      onMouseLeave={resetCursor}
    >
      <h3>Interactive Card</h3>
      <p>Hover to see custom cursor with text</p>
    </div>
  )
}


export function ExampleLoadingButton() {
  const [isLoading, setIsLoading] = useState(false)
  useCursorLoading(isLoading)
  
  const handleClick = async () => {
    setIsLoading(true)
    
    await new Promise(resolve => setTimeout(resolve, 2000))
    setIsLoading(false)
  }
  
  return (
    <Button 
      onClick={handleClick}
      disabled={isLoading}
      className="cursor-interactive"
    >
      {isLoading ? 'Loading...' : 'Click me'}
    </Button>
  )
}


export function ExampleInput() {
  return (
    <input
      type="text"
      placeholder="Type here..."
      className="border p-2 rounded"
      data-cursor="text"
    />
  )
}


export function ExampleDisabledButton() {
  return (
    <Button 
      disabled
      className="cursor-interactive"
      data-cursor="disabled"
    >
      Disabled Button
    </Button>
  )
}
