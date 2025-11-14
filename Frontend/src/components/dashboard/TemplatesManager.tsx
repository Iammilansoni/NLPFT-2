'use client'

import { useState } from 'react'
import { useTemplates, useDeleteTemplate, useSyncTemplates, useReloadTemplates } from '@/hooks/useTemplates'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  Loader2, 
  RefreshCw, 
  Download, 
  Trash2, 
  Plus,
  FileCode,
  AlertCircle
} from 'lucide-react'
import { cn } from '@/lib/utils'

export function TemplatesManager() {
  const { data: templates, isLoading, isError, error } = useTemplates()
  const { mutate: deleteTemplate, isPending: isDeleting } = useDeleteTemplate()
  const { mutate: syncTemplates, isPending: isSyncing } = useSyncTemplates()
  const { mutate: reloadTemplates, isPending: isReloading } = useReloadTemplates()

  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null)

  const handleDelete = (intent: string) => {
    if (confirm(`Are you sure you want to delete the "${intent}" template?`)) {
      deleteTemplate(intent)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <span className="ml-2 text-muted-foreground">Loading templates...</span>
      </div>
    )
  }

  if (isError) {
    return (
      <Card className="border-destructive">
        <CardContent className="pt-6">
          <div className="flex items-center gap-2 text-destructive">
            <AlertCircle className="h-5 w-5" />
            <p>{error?.message || 'Failed to load templates'}</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header Actions */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>API Templates</CardTitle>
              <CardDescription>
                Manage API templates for intent detection and dataset generation
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => syncTemplates()}
                disabled={isSyncing}
              >
                {isSyncing ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Syncing...
                  </>
                ) : (
                  <>
                    <Download className="h-4 w-4 mr-2" />
                    Sync from JSON
                  </>
                )}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => reloadTemplates()}
                disabled={isReloading}
              >
                {isReloading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Reloading...
                  </>
                ) : (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Reload Services
                  </>
                )}
              </Button>
              <Button size="sm">
                <Plus className="h-4 w-4 mr-2" />
                New Template
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Templates Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {templates?.map((template) => (
          <Card
            key={template.api_name}
            className={cn(
              'cursor-pointer transition-all hover:shadow-lg',
              selectedTemplate === template.api_name && 'ring-2 ring-primary'
            )}
            onClick={() => setSelectedTemplate(template.api_name)}
          >
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <FileCode className="h-5 w-5 text-primary" />
                  <CardTitle className="text-lg">{template.api_name}</CardTitle>
                </div>
                <Badge variant="outline" className="text-xs">
                  {template.method}
                </Badge>
              </div>
              <CardDescription className="line-clamp-2">
                {template.description}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="text-xs text-muted-foreground mb-1">Endpoint</div>
                <code className="text-xs bg-muted px-2 py-1 rounded block truncate">
                  {template.endpoint}
                </code>
              </div>

              <div>
                <div className="text-xs text-muted-foreground mb-1">Keywords</div>
                <div className="flex flex-wrap gap-1">
                  {template.intent_keywords.slice(0, 3).map((keyword) => (
                    <Badge key={keyword} variant="secondary" className="text-xs">
                      {keyword}
                    </Badge>
                  ))}
                  {template.intent_keywords.length > 3 && (
                    <Badge variant="secondary" className="text-xs">
                      +{template.intent_keywords.length - 3} more
                    </Badge>
                  )}
                </div>
              </div>

              <div>
                <div className="text-xs text-muted-foreground mb-1">Parameters</div>
                <div className="text-sm">
                  {template.parameters.length} parameter{template.parameters.length !== 1 ? 's' : ''}
                </div>
              </div>

              <div className="flex gap-2 pt-2 border-t">
                <Button
                  variant="outline"
                  size="sm"
                  className="flex-1"
                  onClick={(e) => {
                    e.stopPropagation()
                    // Navigate to edit page
                  }}
                >
                  Edit
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="text-destructive hover:text-destructive"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleDelete(template.api_name)
                  }}
                  disabled={isDeleting}
                >
                  {isDeleting ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Trash2 className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {templates?.length === 0 && (
        <Card>
          <CardContent className="py-12">
            <div className="text-center text-muted-foreground">
              <FileCode className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium mb-2">No templates found</p>
              <p className="text-sm mb-4">
                Get started by syncing from JSON or creating a new template
              </p>
              <div className="flex gap-2 justify-center">
                <Button variant="outline" onClick={() => syncTemplates()}>
                  <Download className="h-4 w-4 mr-2" />
                  Sync from JSON
                </Button>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Template
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
