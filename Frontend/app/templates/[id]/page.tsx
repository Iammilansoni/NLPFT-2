"use client"

import * as React from "react"
import { useParams, useRouter } from "next/navigation"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { motion } from "framer-motion"
import {
  ArrowLeft,
  Edit,
  Trash2,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  FileCode,
  Globe,
  Shield,
  Tag,
  Calendar,
  User,
  Copy,
  ExternalLink,
  Eye,
  EyeOff,
} from "lucide-react"
import { apiClient } from "@/lib/api"
import type { TemplateModel } from "@/lib/api-types"
import { cn, formatDate, toTitleCase } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { ConfidenceBadge } from "@/components/ui/confidence-badge"
import { useToast } from "@/hooks/use-toast"

export default function TemplateDetailPage() {
  const params = useParams()
  const router = useRouter()
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const templateId = params.id as string

  // Fetch template details
  const { data: template, isLoading, error } = useQuery({
    queryKey: ["template", templateId],
    queryFn: () => apiClient.getTemplate(templateId),
    enabled: !!templateId,
  })

  // Toggle between draft and approved state
  const toggleVisibilityMutation = useMutation({
    mutationFn: () => apiClient.toggleTemplateVisibility(templateId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["template", templateId] })
      queryClient.invalidateQueries({ queryKey: ["templates"] })
      const isApproved = data.status === "approved"
      toast({ 
        title: isApproved ? "Template Approved" : "Template Drafted", 
        description: isApproved 
          ? "Template is approved and available for dataset generation." 
          : "Template is in draft state."
      })
    },
    onError: (error: any) => {
      toast({ 
        title: "Toggle Failed", 
        description: error?.detail || error?.message || "Failed to toggle status",
        variant: "destructive"
      })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: () => apiClient.deleteTemplate(templateId),
    onSuccess: () => {
      toast({ title: "Template Deleted", description: "Template has been deleted." })
      router.push("/templates")
    },
    onError: (error: any) => {
      toast({ title: "Delete Failed", description: error?.message || "Only drafts can be deleted", variant: "destructive" })
    },
  })

  const isApproved = template?.status === "approved"

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    toast({ title: "Copied", description: "Copied to clipboard" })
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    )
  }

  if (error || !template) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-2">Template Not Found</h2>
          <p className="text-muted-foreground mb-4">The template you're looking for doesn't exist.</p>
          <Button onClick={() => router.push("/templates")}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Templates
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <motion.header
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="border-b bg-background/95 backdrop-blur sticky top-0 z-40"
      >
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="icon" onClick={() => router.push("/templates")}>
                <ArrowLeft className="h-5 w-5" />
              </Button>
              <div>
                <div className="flex items-center gap-3">
                  <FileCode className="h-6 w-6 text-primary" />
                  <h1 className="text-2xl font-bold">{toTitleCase(template.api_name)}</h1>
                  {isApproved ? (
                    <Badge variant="success" className="gap-1">
                      <CheckCircle className="h-3 w-3" />
                      Approved
                    </Badge>
                  ) : (
                    <Badge variant="secondary" className="gap-1">
                      <Clock className="h-3 w-3" />
                      Draft
                    </Badge>
                  )}
                </div>
                <p className="text-sm text-muted-foreground mt-1">{template.description?.slice(0, 100)}...</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              {/* Draft/Approved Toggle */}
              <div className="flex items-center gap-3 px-4 py-2 rounded-lg border bg-muted/50">
                <div className="flex items-center gap-2">
                  {isApproved ? (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  ) : (
                    <Clock className="h-4 w-4 text-muted-foreground" />
                  )}
                  <Label htmlFor="visibility-toggle" className="text-sm font-medium cursor-pointer">
                    {isApproved ? "Approved" : "Draft"}
                  </Label>
                </div>
                <Switch
                  id="visibility-toggle"
                  checked={isApproved}
                  onCheckedChange={() => toggleVisibilityMutation.mutate()}
                  disabled={toggleVisibilityMutation.isPending}
                />
              </div>

              {/* Edit Button */}
              <Button variant="outline" onClick={() => router.push(`/templates/${templateId}/edit`)}>
                <Edit className="h-4 w-4 mr-2" />
                Edit
              </Button>

              {/* Generate Dataset (only when approved) */}
              {isApproved && (
                <Button onClick={() => router.push(`/datasets?template=${templateId}`)}>
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Generate Dataset
                </Button>
              )}

              {/* Delete (only when draft) */}
              {!isApproved && (
                <Button 
                  variant="outline" 
                  className="text-destructive hover:bg-destructive/10"
                  onClick={() => {
                    if (confirm("Delete this template?")) {
                      deleteMutation.mutate()
                    }
                  }}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete
                </Button>
              )}
            </div>
          </div>
        </div>
      </motion.header>

      {/* Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Endpoint Info */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-card border rounded-xl p-6"
            >
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Globe className="h-5 w-5" />
                API Endpoint
              </h2>
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="font-mono">{template.method}</Badge>
                  <code className="flex-1 bg-muted px-3 py-2 rounded text-sm font-mono truncate">
                    {template.endpoint}
                  </code>
                  <Button variant="ghost" size="icon" onClick={() => copyToClipboard(template.endpoint)}>
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </motion.div>

            {/* Description */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-card border rounded-xl p-6"
            >
              <h2 className="text-lg font-semibold mb-4">Description</h2>
              <p className="text-muted-foreground whitespace-pre-wrap">{template.description}</p>
            </motion.div>

            {/* Parameters */}
            {template.parameters && template.parameters.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="bg-card border rounded-xl p-6"
              >
                <h2 className="text-lg font-semibold mb-4">Parameters ({template.parameters.length})</h2>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-2 px-3">Name</th>
                        <th className="text-left py-2 px-3">Type</th>
                        <th className="text-left py-2 px-3">Required</th>
                        <th className="text-left py-2 px-3">Description</th>
                      </tr>
                    </thead>
                    <tbody>
                      {template.parameters.map((param: any, idx: number) => (
                        <tr key={idx} className="border-b last:border-0">
                          <td className="py-2 px-3 font-mono text-primary">{param.name}</td>
                          <td className="py-2 px-3"><Badge variant="outline">{param.type}</Badge></td>
                          <td className="py-2 px-3">{param.required ? "Yes" : "No"}</td>
                          <td className="py-2 px-3 text-muted-foreground">{param.description || "-"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </motion.div>
            )}

            {/* Sample Requests */}
            {template.sample_requests && template.sample_requests.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="bg-card border rounded-xl p-6"
              >
                <h2 className="text-lg font-semibold mb-4">Sample Requests ({template.sample_requests.length})</h2>
                <div className="space-y-4">
                  {template.sample_requests.map((sample: any, idx: number) => (
                    <div key={idx} className="border rounded-lg p-4">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-medium">Sample #{idx + 1}</span>
                        {sample.note && <span className="text-xs text-muted-foreground">{sample.note}</span>}
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <p className="text-xs text-muted-foreground mb-1">Request</p>
                          <pre className="bg-muted p-3 rounded text-xs overflow-x-auto">
                            {JSON.stringify(sample.request, null, 2)}
                          </pre>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground mb-1">Expected Response</p>
                          <pre className="bg-muted p-3 rounded text-xs overflow-x-auto">
                            {JSON.stringify(sample.expected_response, null, 2)}
                          </pre>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Status */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-card border rounded-xl p-6"
            >
              <h3 className="font-semibold mb-4">Status</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Current State</span>
                  {isApproved ? (
                    <Badge variant="success" className="gap-1">
                      <CheckCircle className="h-3 w-3" />
                      Approved
                    </Badge>
                  ) : (
                    <Badge variant="secondary" className="gap-1">
                      <Clock className="h-3 w-3" />
                      Draft
                    </Badge>
                  )}
                </div>
                <p className="text-xs text-muted-foreground">
                  {isApproved 
                    ? "This template is approved and available for dataset generation." 
                    : "This template is in draft state. Toggle it on to approve and make it available for dataset generation."}
                </p>
                {template.confidence !== undefined && template.confidence > 0 && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Confidence</span>
                    <ConfidenceBadge confidence={template.confidence} />
                  </div>
                )}
              </div>
            </motion.div>

            {/* Security */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-card border rounded-xl p-6"
            >
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <Shield className="h-4 w-4" />
                Security
              </h3>
              <div className="space-y-3">
                <div>
                  <span className="text-xs text-muted-foreground">Classification</span>
                  <p className="font-medium">{template.security_classification || "Public"}</p>
                </div>
                {template.requires_auth !== undefined && (
                  <div>
                    <span className="text-xs text-muted-foreground">Authentication</span>
                    <p className="font-medium">{template.requires_auth ? "Required" : "Not Required"}</p>
                  </div>
                )}
              </div>
            </motion.div>

            {/* Keywords */}
            {template.intent_keywords && template.intent_keywords.length > 0 && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
                className="bg-card border rounded-xl p-6"
              >
                <h3 className="font-semibold mb-4 flex items-center gap-2">
                  <Tag className="h-4 w-4" />
                  Intent Keywords
                </h3>
                <div className="flex flex-wrap gap-2">
                  {template.intent_keywords.map((keyword: string) => (
                    <Badge key={keyword} variant="secondary">{keyword}</Badge>
                  ))}
                </div>
              </motion.div>
            )}

            {/* Metadata */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-card border rounded-xl p-6"
            >
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Details
              </h3>
              <div className="space-y-3 text-sm">
                {template.created_at && (
                  <div>
                    <span className="text-muted-foreground">Created</span>
                    <p>{formatDate(template.created_at)}</p>
                  </div>
                )}
                {template.updated_at && (
                  <div>
                    <span className="text-muted-foreground">Updated</span>
                    <p>{formatDate(template.updated_at)}</p>
                  </div>
                )}
                {template.template_id && (
                  <div>
                    <span className="text-muted-foreground">ID</span>
                    <p className="font-mono text-xs truncate">{template.template_id}</p>
                  </div>
                )}
              </div>
            </motion.div>
          </div>
        </div>
      </main>
    </div>
  )
}
