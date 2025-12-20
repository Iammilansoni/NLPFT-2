"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { TemplateForm } from "@/components/TemplateForm"
import { useAuth } from "@/contexts/AuthContext"
import { Loader2 } from "lucide-react"

export default function NewTemplatePage() {
  const router = useRouter()
  const { user, isLoading, isAuthenticated } = useAuth()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth/login')
    }
  }, [isLoading, isAuthenticated, router])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return null
  }

  const userId = user.user_id
  const userRole = user.is_expert ? "expert" : "user"

  return (
    <TemplateForm
      mode="create"
      userId={userId}
      userRole={userRole}
    />
  )
}
