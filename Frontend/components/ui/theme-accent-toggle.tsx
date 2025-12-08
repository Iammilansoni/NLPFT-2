'use client'

import { useState, useEffect } from 'react'
import { Palette } from 'lucide-react'
import { Button } from './button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from './dropdown-menu'

const accents = [
  { name: 'Violet', value: 'violet', color: 'rgb(124 58 237)' },
  { name: 'Teal', value: 'teal', color: 'rgb(6 182 212)' },
  { name: 'Emerald', value: 'emerald', color: 'rgb(16 185 129)' },
]

export function ThemeAccentToggle() {
  const [currentAccent, setCurrentAccent] = useState('violet')
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    const accent = document.documentElement.getAttribute('data-accent') || 'violet'
    setCurrentAccent(accent)
  }, [])

  const handleAccentChange = (accent: string) => {
    document.documentElement.setAttribute('data-accent', accent)
    setCurrentAccent(accent)
    localStorage.setItem('accent', accent)
  }

  if (!mounted) {
    return (
      <Button variant="ghost" size="icon" className="h-9 w-9">
        <Palette className="h-4 w-4" />
      </Button>
    )
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="h-9 w-9">
          <Palette className="h-4 w-4" />
          <span className="sr-only">Change accent color</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {accents.map((accent) => (
          <DropdownMenuItem
            key={accent.value}
            onClick={() => handleAccentChange(accent.value)}
            className="flex items-center gap-3"
          >
            <div
              className="h-4 w-4 rounded-full border-2"
              style={{ backgroundColor: accent.color }}
            />
            <span>{accent.name}</span>
            {currentAccent === accent.value && (
              <span className="ml-auto text-xs">✓</span>
            )}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
