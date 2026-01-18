'use client'

import { useState } from 'react'
import { Download, FileJson, FileSpreadsheet, Loader2, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useToast } from '@/hooks/use-toast'

interface DataExportButtonProps {
  data: any[] | Record<string, any>
  filename: string
  disabled?: boolean
  variant?: 'default' | 'outline' | 'ghost'
  size?: 'default' | 'sm' | 'lg' | 'icon'
  label?: string
}

/**
 * Data Export Button Component
 * Exports data as CSV or JSON with a dropdown menu
 */
export function DataExportButton({
  data,
  filename,
  disabled = false,
  variant = 'outline',
  size = 'sm',
  label = 'Export'
}: DataExportButtonProps) {
  const { toast } = useToast()
  const [isExporting, setIsExporting] = useState(false)
  const [exportComplete, setExportComplete] = useState<'csv' | 'json' | null>(null)

  // Convert data to CSV string
  const convertToCSV = (data: any[]): string => {
    if (!data || data.length === 0) return ''
    
    // Get headers from first object
    const headers = Object.keys(data[0])
    
    // Create header row
    const headerRow = headers.map(h => `"${h}"`).join(',')
    
    // Create data rows
    const dataRows = data.map(row => {
      return headers.map(header => {
        const value = row[header]
        if (value === null || value === undefined) return ''
        if (typeof value === 'object') return `"${JSON.stringify(value).replace(/"/g, '""')}"`
        if (typeof value === 'string') return `"${value.replace(/"/g, '""')}"`
        return value
      }).join(',')
    })
    
    return [headerRow, ...dataRows].join('\n')
  }

  // Download file
  const downloadFile = (content: string, mimeType: string, extension: string) => {
    const blob = new Blob([content], { type: mimeType })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${filename}_${new Date().toISOString().split('T')[0]}.${extension}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  // Export as CSV
  const handleExportCSV = async () => {
    setIsExporting(true)
    try {
      const dataArray = Array.isArray(data) ? data : [data]
      const csv = convertToCSV(dataArray)
      downloadFile(csv, 'text/csv;charset=utf-8', 'csv')
      setExportComplete('csv')
      toast({
        title: 'Export Complete',
        description: `${dataArray.length} records exported as CSV`,
      })
      setTimeout(() => setExportComplete(null), 2000)
    } catch (error) {
      toast({
        title: 'Export Failed',
        description: 'Failed to export data as CSV',
        variant: 'destructive',
      })
    } finally {
      setIsExporting(false)
    }
  }

  // Export as JSON
  const handleExportJSON = async () => {
    setIsExporting(true)
    try {
      const jsonString = JSON.stringify(data, null, 2)
      downloadFile(jsonString, 'application/json', 'json')
      setExportComplete('json')
      const count = Array.isArray(data) ? data.length : 1
      toast({
        title: 'Export Complete',
        description: `${count} record(s) exported as JSON`,
      })
      setTimeout(() => setExportComplete(null), 2000)
    } catch (error) {
      toast({
        title: 'Export Failed',
        description: 'Failed to export data as JSON',
        variant: 'destructive',
      })
    } finally {
      setIsExporting(false)
    }
  }

  const isEmpty = !data || (Array.isArray(data) && data.length === 0)

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant={variant}
          size={size}
          disabled={disabled || isEmpty || isExporting}
          className="gap-2"
        >
          {isExporting ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : exportComplete ? (
            <Check className="h-4 w-4 text-success" />
          ) : (
            <Download className="h-4 w-4" />
          )}
          {label}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-40">
        <DropdownMenuItem onClick={handleExportCSV} className="gap-2 cursor-pointer">
          <FileSpreadsheet className="h-4 w-4" />
          Export as CSV
        </DropdownMenuItem>
        <DropdownMenuItem onClick={handleExportJSON} className="gap-2 cursor-pointer">
          <FileJson className="h-4 w-4" />
          Export as JSON
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

// Utility function to export data programmatically
export function exportToCSV(data: any[], filename: string) {
  if (!data || data.length === 0) return
  
  const headers = Object.keys(data[0])
  const headerRow = headers.map(h => `"${h}"`).join(',')
  const dataRows = data.map(row => {
    return headers.map(header => {
      const value = row[header]
      if (value === null || value === undefined) return ''
      if (typeof value === 'object') return `"${JSON.stringify(value).replace(/"/g, '""')}"`
      if (typeof value === 'string') return `"${value.replace(/"/g, '""')}"`
      return value
    }).join(',')
  })
  
  const csv = [headerRow, ...dataRows].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${filename}_${new Date().toISOString().split('T')[0]}.csv`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

export function exportToJSON(data: any, filename: string) {
  const jsonString = JSON.stringify(data, null, 2)
  const blob = new Blob([jsonString], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${filename}_${new Date().toISOString().split('T')[0]}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

export default DataExportButton
