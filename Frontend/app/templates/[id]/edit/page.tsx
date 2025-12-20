"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { TemplateForm } from "@/components/TemplateForm"
import { apiClient } from "@/lib/api"
import { useAuth } from "@/contexts/AuthContext"
import { Loader2 } from "lucide-react"

export default function EditTemplatePage() {
  const params = useParams()
  const router = useRouter()
  const templateId = params.id as string
  const { user, isLoading: authLoading, isAuthenticated } = useAuth()

  const [template, setTemplate] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/auth/login')
    }
  }, [authLoading, isAuthenticated, router])

  useEffect(() => {
    async function loadTemplate() {
      try {
        setLoading(true)
        const data = await apiClient.getTemplate(templateId)
        setTemplate(data)
      } catch (err: any) {
        console.error("Failed to load template:", err)
        setError(err?.message || "Failed to load template")
      } finally {
        setLoading(false)
      }
    }

    if (templateId) {
      loadTemplate()
    }
  }, [templateId])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-muted-foreground">Loading template...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-4 text-center">
          <div className="text-destructive text-lg font-semibold">Error loading template</div>
          <p className="text-muted-foreground">{error}</p>
          <button
            onClick={() => router.push("/templates")}
            className="text-primary hover:underline"
          >
            Back to Templates
          </button>
        </div>
      </div>
    )
  }

  if (!template) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-4 text-center">
          <div className="text-lg font-semibold">Template not found</div>
          <button
            onClick={() => router.push("/templates")}
            className="text-primary hover:underline"
          >
            Back to Templates
          </button>
        </div>
      </div>
    )
  }

  // Transform API response to match TemplateForm initialData format
  // Backend returns sample_requests as: { scenario, request, expected_response }
  // Form expects: { request, expected_response, note }
  const transformedSampleRequests = (template.sample_requests || []).map((sr: any) => ({
    request: sr.request || {},
    expected_response: sr.expected_response || {},
    note: sr.scenario || sr.note || '',
  }));

  const initialData = {
    template_id: template.template_id,
    api_name: template.api_name,
    description: template.description,
    base_url: template.base_url,
    method: template.method,
    headers: template.headers || {},
    json_schema: template.json_schema || {},
    sample_requests: transformedSampleRequests,
    side_effects: template.side_effects || '',
    domain_tags: template.domain_tags || template.intent_keywords || [],
    status: template.status || 'draft',
    reviewer_notes: template.reviewer_notes || template.expert_notes || '',
    parameters: template.parameters || [],
    expected_responses: template.expected_responses || [],
  }

  // Get user info from auth context
  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-muted-foreground">Authenticating...</p>
        </div>
      </div>
    )
  }

  const userId = user.user_id
  const userRole = user.is_expert ? "expert" : "user"

  return (
    <TemplateForm
      mode="edit"
      initialData={initialData}
      userId={userId}
      userRole={userRole}
      onSuccess={() => router.push("/templates")}
    />
  )
}
