"use client"

import { useState, useEffect, useId } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  User,
  Cpu,
  Loader2,
  Check,
  AlertTriangle,
  Shield,
  ChevronRight,
  Lock,
  Trash2,
  Mail,
  UserCircle,
  Zap,
  Sparkles,
  Copy,
  Calendar,
  Activity,
  Clock,
  Bell,
  Monitor,
  Info,
  Database,
  Server,
  ArrowRight,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Plus,
  Layers,
  Eye,
  EyeOff,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { toast } from '@/hooks/use-toast'
import { cn } from '@/lib/utils'
import { apiClient } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'
import authService from '@/lib/auth'
import { DEFAULT_EMBEDDING_MODEL, formatModelName } from '@/lib/constants/embedding-models'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { OnboardingTour } from '@/components/onboarding/OnboardingTour'
import { LLMProviderSettings } from '@/components/settings/LLMProviderSettings'
import { EmbeddingModelPicker } from '@/components/settings/EmbeddingModelPicker'

// ============================================================================
// NAVIGATION ITEMS
// ============================================================================

const NAV_ITEMS = [
  { id: 'profile', label: 'Profile', icon: UserCircle, description: 'Manage your account information', color: 'from-blue-500 to-indigo-600' },
  { id: 'security', label: 'Security', icon: Shield, description: 'Password, 2FA, and sessions', color: 'from-emerald-500 to-teal-600' },
  { id: 'llm-providers', label: 'AI Providers', icon: Sparkles, description: 'Configure LLM integrations', color: 'from-purple-500 to-violet-600' },
  { id: 'models', label: 'Embeddings', icon: Layers, description: 'Vector embedding settings', color: 'from-orange-500 to-amber-600' },
] as const

type TabValue = typeof NAV_ITEMS[number]['id']

// ============================================================================
// STATS CARD COMPONENT
// ============================================================================

interface StatsCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: React.ElementType
  gradient: string
}

const StatsCard = ({ title, value, subtitle, icon: Icon, gradient }: StatsCardProps) => (
  <div className="relative group">
    <div className="absolute -inset-0.5 bg-gradient-to-r opacity-0 group-hover:opacity-50 blur-xl transition-all duration-700 rounded-2xl"
         style={{ backgroundImage: `linear-gradient(to right, var(--tw-gradient-stops))` }} />
    <div className="relative rounded-2xl border border-border/40 bg-card/80 backdrop-blur-xl p-5 hover:border-border/60 transition-all duration-300">
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <p className="text-2xl font-bold text-foreground">{value}</p>
          {subtitle && (
            <p className="text-xs text-muted-foreground">{subtitle}</p>
          )}
        </div>
        <div className={cn("p-3 rounded-xl bg-gradient-to-br shadow-lg", gradient)}>
          <Icon className="h-5 w-5 text-white" />
        </div>
      </div>
    </div>
  </div>
)

// ============================================================================
// SECTION CARD COMPONENT
// ============================================================================

interface SectionCardProps {
  title: string
  description?: string
  icon?: React.ElementType
  children: React.ReactNode
  action?: React.ReactNode
  className?: string
  gradient?: string
}

const SectionCard = ({ title, description, icon: Icon, children, action, className, gradient }: SectionCardProps) => (
  <div className={cn(
    "rounded-2xl border border-border/40 bg-card/80 backdrop-blur-xl overflow-hidden shadow-sm hover:shadow-md transition-all duration-300",
    className
  )}>
    <div className="flex items-center justify-between px-6 py-4 border-b border-border/40 bg-gradient-to-r from-muted/30 to-transparent">
      <div className="flex items-center gap-3">
        {Icon && (
          <div className={cn(
            "p-2.5 rounded-xl shadow-sm",
            gradient ? `bg-gradient-to-br ${gradient}` : "bg-primary/10"
          )}>
            <Icon className={cn("h-4 w-4", gradient ? "text-white" : "text-primary")} />
          </div>
        )}
        <div>
          <h3 className="font-semibold text-foreground">{title}</h3>
          {description && (
            <p className="text-sm text-muted-foreground">{description}</p>
          )}
        </div>
      </div>
      {action}
    </div>
    <div className="p-6">{children}</div>
  </div>
)

// ============================================================================
// SETTING ROW COMPONENT  
// ============================================================================

interface SettingRowProps {
  icon: React.ElementType
  title: string
  description: string
  children: React.ReactNode
  iconColor?: string
  iconBg?: string
}

const SettingRow = ({ icon: Icon, title, description, children, iconColor = "text-muted-foreground", iconBg = "bg-muted/50" }: SettingRowProps) => (
  <div className="flex items-center justify-between py-5 first:pt-0 last:pb-0 border-b border-border/30 last:border-0 group">
    <div className="flex items-center gap-4">
      <div className={cn("p-3 rounded-xl transition-all duration-300 group-hover:scale-105", iconBg)}>
        <Icon className={cn("h-5 w-5", iconColor)} />
      </div>
      <div>
        <p className="font-medium text-foreground">{title}</p>
        <p className="text-sm text-muted-foreground max-w-md">{description}</p>
      </div>
    </div>
    <div>{children}</div>
  </div>
)

// ============================================================================
// MODEL SELECTION CARD (Dynamic from API)
// ============================================================================

interface RegisteredModel {
  name: string
  display_name: string
  dimension: number | null
  size?: string
  is_registered: boolean
  is_local: boolean
}

interface ModelCardProps {
  model: RegisteredModel
  isSelected: boolean
  isCurrentlyActive: boolean
  onSelect: () => void
}

const ModelCard = ({ model, isSelected, isCurrentlyActive, onSelect }: ModelCardProps) => {
  return (
    <button
      onClick={onSelect}
      className={cn(
        "relative w-full text-left rounded-2xl border p-5 group",
        "bg-card/60 backdrop-blur-sm",
        "transition-all duration-300 ease-out",
        "hover:shadow-lg hover:shadow-primary/5 hover:-translate-y-0.5",
        "active:scale-[0.995]",
        isSelected
          ? "border-primary bg-gradient-to-br from-primary/10 via-primary/5 to-transparent ring-2 ring-primary/30 shadow-lg shadow-primary/10"
          : "border-border/40 hover:border-border/60"
      )}
    >
      {isSelected && (
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_var(--tw-gradient-stops))] from-primary/10 via-transparent to-transparent rounded-2xl" />
      )}

      <div className="relative flex items-center justify-between gap-4">
        <div className="flex items-center gap-4 flex-1 min-w-0">
          {/* Model Icon */}
          <div className={cn(
            "p-3 rounded-xl transition-all duration-300",
            isSelected 
              ? "bg-primary/20 ring-2 ring-primary/20" 
              : "bg-muted/50 group-hover:bg-muted/80"
          )}>
            <Database className={cn(
              "h-5 w-5 transition-colors",
              isSelected ? "text-primary" : "text-muted-foreground"
            )} />
          </div>

          {/* Model Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 flex-wrap">
              <h3 className="text-base font-semibold text-foreground truncate">
                {model.display_name || formatModelName(model.name)}
              </h3>
              {model.dimension && (
                <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-muted/80 text-muted-foreground border border-border/50">
                  {model.dimension}D
                </span>
              )}
              {isCurrentlyActive && !isSelected && (
                <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-600 border border-emerald-500/20 flex items-center gap-1">
                  <CheckCircle2 className="h-3 w-3" />
                  Active
                </span>
              )}
            </div>
            {model.size && (
              <p className="text-xs text-muted-foreground mt-1">{model.size}</p>
            )}
          </div>
        </div>

        {/* Selection indicator */}
        <div className={cn(
          "flex-shrink-0 w-7 h-7 rounded-full border-2 flex items-center justify-center transition-all duration-300",
          isSelected
            ? "border-primary bg-primary shadow-lg shadow-primary/30"
            : "border-muted-foreground/20 group-hover:border-muted-foreground/40"
        )}>
          {isSelected && <Check className="h-3.5 w-3.5 text-primary-foreground" strokeWidth={3} />}
        </div>
      </div>
    </button>
  )
}

// ============================================================================
// NAVIGATION ITEM COMPONENT
// ============================================================================

interface NavItemProps {
  item: typeof NAV_ITEMS[number]
  isActive: boolean
  onClick: () => void
}

const NavItem = ({ item, isActive, onClick }: NavItemProps) => {
  const Icon = item.icon
  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full flex items-center gap-4 px-4 py-4 rounded-xl text-left relative overflow-hidden",
        "transition-all duration-300 group",
        isActive
          ? "bg-gradient-to-r from-primary to-primary/90 text-primary-foreground shadow-lg shadow-primary/30"
          : "hover:bg-muted/60 text-foreground"
      )}
    >
      {/* Active indicator line */}
      {isActive && (
        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-primary-foreground/40 rounded-r-full" />
      )}
      
      <div className={cn(
        "p-2.5 rounded-xl transition-all duration-300",
        isActive 
          ? "bg-primary-foreground/20" 
          : cn("bg-gradient-to-br", item.color, "opacity-80 group-hover:opacity-100 group-hover:scale-105 shadow-md")
      )}>
        <Icon className={cn(
          "h-4 w-4",
          isActive ? "text-primary-foreground" : "text-white"
        )} />
      </div>
      <div className="flex-1 min-w-0">
        <p className={cn(
          "font-semibold text-sm",
          isActive ? "text-primary-foreground" : "text-foreground"
        )}>{item.label}</p>
        <p className={cn(
          "text-xs truncate",
          isActive ? "text-primary-foreground/70" : "text-muted-foreground"
        )}>{item.description}</p>
      </div>
      <ChevronRight className={cn(
        "h-4 w-4 transition-transform duration-300",
        isActive ? "text-primary-foreground translate-x-1" : "text-muted-foreground/40 group-hover:translate-x-1 group-hover:text-muted-foreground"
      )} />
    </button>
  )
}

// ============================================================================
// MAIN SETTINGS PAGE
// ============================================================================

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<TabValue>('profile')
  const [selectedModel, setSelectedModel] = useState('')
  const queryClient = useQueryClient()
  const { user, isLoading: authLoading } = useAuth()

  // Profile form state
  const [profileForm, setProfileForm] = useState({
    username: '',
    email: '',
  })
  const [isProfileSaving, setIsProfileSaving] = useState(false)

  // Password change state
  const [isPasswordDialogOpen, setIsPasswordDialogOpen] = useState(false)
  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  })
  const [isPasswordChanging, setIsPasswordChanging] = useState(false)
  const [passwordError, setPasswordError] = useState('')
  const [showCurrentPassword, setShowCurrentPassword] = useState(false)
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)

  // Model change confirmation dialog state
  const [isModelConfirmDialogOpen, setIsModelConfirmDialogOpen] = useState(false)
  
  // Ollama health status
  const [ollamaStatus, setOllamaStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking')
  
  // Security alerts state - initialize from localStorage
  const [securityAlertsEnabled, setSecurityAlertsEnabled] = useState(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('securityAlertsEnabled')
      return stored !== null ? stored === 'true' : true
    }
    return true
  })
  
  const [reembeddingImpact, setReembeddingImpact] = useState<{
    impact: 'none' | 'low' | 'medium' | 'high';
    message: string;
    affected_datasets: Array<{
      dataset_id: string;
      name: string;
      embedding_count: number;
      embedding_model: string;
    }>;
    reembedding_required: boolean;
    total_embeddings_affected?: number;
  } | null>(null)
  const [isLoadingImpact, setIsLoadingImpact] = useState(false)

  // Update form when user loads
  useEffect(() => {
    if (user) {
      setProfileForm({
        username: user.username || '',
        email: user.email || '',
      })
    }
  }, [user])

  // Check Ollama health status
  useEffect(() => {
    const checkOllamaHealth = async () => {
      setOllamaStatus('checking')
      try {
        // Check Ollama directly via the backend's embedding models endpoint
        // This indirectly verifies Ollama is running since it queries Ollama
        const response = await apiClient.listEmbeddingModels()
        // If we get a response with models data, Ollama is likely connected
        setOllamaStatus(response?.models ? 'connected' : 'disconnected')
      } catch (error) {
        setOllamaStatus('disconnected')
      }
    }
    
    checkOllamaHealth()
    // Re-check every 30 seconds
    const interval = setInterval(checkOllamaHealth, 30000)
    return () => clearInterval(interval)
  }, [])

  // Handle password change
  const handlePasswordChange = async () => {
    setPasswordError('')

    if (!passwordForm.current_password || !passwordForm.new_password || !passwordForm.confirm_password) {
      setPasswordError('All fields are required')
      return
    }

    if (passwordForm.new_password.length < 8) {
      setPasswordError('New password must be at least 8 characters')
      return
    }

    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setPasswordError('New passwords do not match')
      return
    }

    if (!/[A-Z]/.test(passwordForm.new_password)) {
      setPasswordError('Password must contain at least one uppercase letter')
      return
    }
    if (!/[a-z]/.test(passwordForm.new_password)) {
      setPasswordError('Password must contain at least one lowercase letter')
      return
    }
    if (!/[0-9]/.test(passwordForm.new_password)) {
      setPasswordError('Password must contain at least one digit')
      return
    }

    setIsPasswordChanging(true)
    try {
      await authService.changePassword({
        current_password: passwordForm.current_password,
        new_password: passwordForm.new_password,
        confirm_password: passwordForm.confirm_password,
      })

      toast({
        title: "Password Updated",
        description: "Your password has been changed successfully.",
      })

      setIsPasswordDialogOpen(false)
      setPasswordForm({ current_password: '', new_password: '', confirm_password: '' })
    } catch (error: any) {
      const errorMessage = error?.response?.data?.detail || error?.message || 'Failed to change password'
      setPasswordError(errorMessage)
      toast({
        title: "Password Change Failed",
        description: errorMessage,
        variant: "destructive",
      })
    } finally {
      setIsPasswordChanging(false)
    }
  }

  // Fetch user settings
  const { data: settings, isLoading: settingsLoading } = useQuery({
    queryKey: ['userSettings'],
    queryFn: () => apiClient.getUserSettings(),
  })

  // Fetch registered embedding models from API
  const { data: embeddingModelsData, isLoading: embeddingModelsLoading, refetch: refetchEmbeddingModels } = useQuery({
    queryKey: ['embedding-models-available'],
    queryFn: () => apiClient.listEmbeddingModels(),
    staleTime: 60000,
  })

  // Get only registered models for selection
  const registeredModels = (embeddingModelsData?.models || []).filter(m => m.is_registered)

  // Update selected model when settings load
  useEffect(() => {
    if (settings?.default_embedding_model) {
      setSelectedModel(settings.default_embedding_model)
    } else {
      setSelectedModel(DEFAULT_EMBEDDING_MODEL)
    }
  }, [settings])

  // Find current model info from API data
  const getModelInfo = (modelName: string) => {
    return registeredModels.find(m => m.name === modelName)
  }

  // Mutation to update settings
  const updateSettingsMutation = useMutation({
    mutationFn: (data: { default_embedding_model?: string; embedding_dimension?: number }) =>
      apiClient.updateUserSettings(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['userSettings'] })
      const modelInfo = getModelInfo(selectedModel)
      toast({
        title: "Settings Saved",
        description: `Default model updated to ${modelInfo?.display_name || formatModelName(selectedModel)}`,
      })
    },
    onError: (error: any) => {
      toast({
        title: "Update Failed",
        description: error?.detail || "Failed to update settings",
        variant: "destructive",
      })
    },
  })

  const handleSaveModel = async () => {
    const model = getModelInfo(selectedModel)
    if (!model || !model.dimension) {
      toast({
        title: "Invalid Model",
        description: "Please select a registered model with known dimensions",
        variant: "destructive",
      })
      return
    }

    if (settings?.default_embedding_model && settings.default_embedding_model !== selectedModel) {
      setIsLoadingImpact(true)
      try {
        const impact = await apiClient.checkReembeddingImpact(selectedModel)
        setReembeddingImpact(impact)
      } catch (error) {
        console.error('Failed to check re-embedding impact:', error)
        setReembeddingImpact(null)
      } finally {
        setIsLoadingImpact(false)
      }
      setIsModelConfirmDialogOpen(true)
    } else {
      updateSettingsMutation.mutate({
        default_embedding_model: selectedModel,
        embedding_dimension: model.dimension
      })
    }
  }

  const handleConfirmModelChange = () => {
    const model = getModelInfo(selectedModel)
    if (model && model.dimension) {
      updateSettingsMutation.mutate({
        default_embedding_model: selectedModel,
        embedding_dimension: model.dimension
      })
    }
    setIsModelConfirmDialogOpen(false)
  }

  const hasModelChanged = settings?.default_embedding_model !== selectedModel

  // Copy to clipboard utility
  const copyToClipboard = async (text: string, label: string) => {
    try {
      await navigator.clipboard.writeText(text)
      toast({ title: "Copied!", description: `${label} copied to clipboard` })
    } catch (error) {
      toast({ 
        title: "Copy failed", 
        description: error instanceof Error ? error.message : "Unable to copy to clipboard",
        variant: "destructive"
      })
    }
  }

  // ============================================================================
  // RENDER SECTIONS
  // ============================================================================

  const renderProfileSection = () => (
    <div className="space-y-6">
      {/* Profile Hero Card */}
      <div className="relative overflow-hidden rounded-3xl border border-border/40 bg-gradient-to-br from-card via-card to-muted/30">
        {/* Decorative background elements */}
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-gradient-to-bl from-primary/20 via-primary/5 to-transparent rounded-full blur-3xl -translate-y-1/2 translate-x-1/3" />
        <div className="absolute bottom-0 left-0 w-[300px] h-[300px] bg-gradient-to-tr from-blue-500/10 via-transparent to-transparent rounded-full blur-3xl translate-y-1/2 -translate-x-1/4" />
        
        <div className="relative p-8 lg:p-10">
          {authLoading ? (
            <div className="flex items-center justify-center py-20">
              <div className="relative">
                <Loader2 className="h-10 w-10 animate-spin text-primary/50" />
                <div className="absolute inset-0 h-10 w-10 animate-ping bg-primary/20 rounded-full" />
              </div>
            </div>
          ) : user ? (
            <div className="flex flex-col lg:flex-row items-start lg:items-center gap-8">
              {/* Avatar with status */}
              <div className="relative group">
                <div className="absolute -inset-1 bg-gradient-to-br from-primary via-primary/50 to-primary/20 rounded-[28px] blur opacity-60 group-hover:opacity-80 transition-opacity duration-300" />
                <div className="relative h-32 w-32 rounded-[24px] bg-gradient-to-br from-primary via-primary to-primary/80 flex items-center justify-center text-5xl font-bold text-primary-foreground shadow-2xl">
                  {user.username ? user.username.charAt(0).toUpperCase() : user.email.charAt(0).toUpperCase()}
                </div>
                <div className="absolute -bottom-2 -right-2 p-2.5 bg-emerald-500 rounded-xl shadow-lg shadow-emerald-500/30 ring-4 ring-card">
                  <CheckCircle2 className="h-4 w-4 text-white" />
                </div>
              </div>

              {/* User Info */}
              <div className="flex-1">
                <div className="flex items-center gap-3 flex-wrap">
                  <h2 className="text-4xl font-bold text-foreground">{user.username || 'User'}</h2>
                  {user.is_expert && (
                    <span className="text-xs font-bold px-4 py-1.5 rounded-full bg-gradient-to-r from-amber-500/20 to-orange-500/20 text-amber-600 dark:text-amber-400 border border-amber-500/30 shadow-sm">
                      ✦ Expert
                    </span>
                  )}
                  <span className="text-xs font-semibold px-4 py-1.5 rounded-full bg-emerald-500/10 text-emerald-600 border border-emerald-500/20">
                    ● Verified
                  </span>
                </div>
                <p className="text-muted-foreground mt-3 flex items-center gap-2 text-lg">
                  <Mail className="h-5 w-5" />
                  {user.email}
                </p>
                <div className="flex items-center gap-6 mt-5 text-sm text-muted-foreground">
                  <span className="flex items-center gap-2 px-4 py-2 rounded-full bg-muted/30 backdrop-blur-sm">
                    <Calendar className="h-4 w-4" />
                    Joined {new Date(user.created_at || Date.now()).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
                  </span>
                  <span className="flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10">
                    <div className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                    </div>
                    <span className="text-emerald-600">Active now</span>
                  </span>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-20">
              <div className="mx-auto w-24 h-24 rounded-3xl bg-muted/50 flex items-center justify-center mb-6">
                <User className="h-12 w-12 text-muted-foreground/30" />
              </div>
              <p className="text-xl text-muted-foreground">Please log in to view your profile</p>
            </div>
          )}
        </div>
      </div>

      {/* Account Information */}
      {user && (
        <SectionCard 
          title="Account Information" 
          description="Manage your personal details and preferences"
          icon={UserCircle}
          gradient="from-blue-500 to-indigo-600"
        >
          <div className="grid gap-6">
            <div className="grid md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label htmlFor="username" className="text-sm font-semibold">
                  Username
                </Label>
                <Input
                  id="username"
                  value={profileForm.username}
                  onChange={(e) => setProfileForm(prev => ({ ...prev, username: e.target.value }))}
                  placeholder="Your username"
                  className="h-12 bg-muted/30 border-border/40 focus:border-primary/50 focus:ring-2 focus:ring-primary/20 transition-all rounded-xl"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email" className="text-sm font-semibold">
                  Email Address
                </Label>
                <Input
                  id="email"
                  type="email"
                  value={profileForm.email}
                  disabled
                  className="h-12 bg-muted/50 cursor-not-allowed rounded-xl"
                />
                <p className="text-xs text-muted-foreground flex items-center gap-1">
                  <Lock className="h-3 w-3" />
                  Email cannot be changed for security reasons
                </p>
              </div>
            </div>
            
            <div className="space-y-2">
              <Label className="text-sm font-semibold">User ID</Label>
              <div className="flex items-center gap-3">
                <Input
                  value={user.user_id}
                  disabled
                  className="h-12 bg-muted/50 cursor-not-allowed font-mono text-xs flex-1 rounded-xl"
                />
                <Button
                  variant="outline"
                  size="icon"
                  className="h-12 w-12 rounded-xl hover:bg-primary/5 hover:border-primary/30 transition-colors"
                  onClick={() => copyToClipboard(user.user_id, 'User ID')}
                >
                  <Copy className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between pt-6 mt-6 border-t border-border/30">
            <div className="flex items-center gap-2 text-sm">
              {profileForm.username !== user.username ? (
                <>
                  <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                  <span className="text-amber-600 font-medium">Unsaved changes</span>
                </>
              ) : (
                <>
                  <div className="w-2 h-2 rounded-full bg-emerald-500" />
                  <span className="text-muted-foreground">All changes saved</span>
                </>
              )}
            </div>
            <Button
              disabled={profileForm.username === user.username || isProfileSaving}
              onClick={() => {
                toast({
                  title: "Coming Soon",
                  description: "Profile update functionality will be available soon.",
                })
              }}
              className="min-w-[140px] rounded-xl h-11"
            >
              {isProfileSaving ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  Save Changes
                  <ArrowRight className="h-4 w-4 ml-2" />
                </>
              )}
            </Button>
          </div>
        </SectionCard>
      )}
    </div>
  )

  const renderSecuritySection = () => (
    <div className="space-y-6">
      {/* Security Stats - Placeholder */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatsCard
          title="Security Score"
          value="Good"
          subtitle="Password configured • Placeholder"
          icon={Shield}
          gradient="from-emerald-500 to-teal-600"
        />
        <StatsCard
          title="Last Login"
          value="Current Session"
          subtitle="Security stats coming soon"
          icon={Clock}
          gradient="from-blue-500 to-indigo-600"
        />
        <StatsCard
          title="Active Sessions"
          value="—"
          subtitle="Session tracking coming soon"
          icon={Monitor}
          gradient="from-purple-500 to-violet-600"
        />
      </div>

      {/* Authentication Settings */}
      <SectionCard
        title="Authentication"
        description="Manage your password and security settings"
        icon={Shield}
        gradient="from-emerald-500 to-teal-600"
      >
        <div className="space-y-1">
          <SettingRow
            icon={Lock}
            title="Password"
            description="Use a strong password that you don't use elsewhere"
            iconColor="text-blue-500"
            iconBg="bg-blue-500/10"
          >
            <Button
              variant="outline"
              onClick={() => setIsPasswordDialogOpen(true)}
              className="rounded-xl"
            >
              Change Password
            </Button>
          </SettingRow>

          <SettingRow
            icon={Bell}
            title="Security Alerts"
            description="Get notified about suspicious account activity"
            iconColor="text-amber-500"
            iconBg="bg-amber-500/10"
          >
            <div className="flex items-center gap-2">
              <Switch 
                checked={securityAlertsEnabled}
                onCheckedChange={(checked) => {
                  setSecurityAlertsEnabled(checked)
                  if (typeof window !== 'undefined') {
                    localStorage.setItem('securityAlertsEnabled', String(checked))
                  }
                  toast({
                    title: checked ? "Security Alerts Enabled" : "Security Alerts Disabled",
                    description: "Your preference has been saved.",
                  })
                }}
                disabled={false}
              />
            </div>
          </SettingRow>
        </div>
      </SectionCard>

      {/* Active Sessions */}
      <SectionCard
        title="Active Sessions"
        description="Manage devices where you're logged in"
        icon={Monitor}
        gradient="from-purple-500 to-violet-600"
      >
        <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-xl bg-emerald-500/10">
                <Monitor className="h-5 w-5 text-emerald-500" />
              </div>
              <div>
                <p className="font-medium text-foreground flex items-center gap-2">
                  Current Device
                  <span className="text-xs font-semibold text-emerald-600 bg-emerald-500/10 px-2 py-0.5 rounded-full">
                    Active
                  </span>
                </p>
                <p className="text-sm text-muted-foreground">Chrome on Linux • Last active now</p>
              </div>
            </div>
            <span className="text-xs text-muted-foreground">This device</span>
          </div>
        </div>
      </SectionCard>

      {/* Danger Zone */}
      <SectionCard
        title="Danger Zone"
        description="Irreversible and destructive actions"
        icon={AlertTriangle}
        className="border-red-500/20"
        gradient="from-red-500 to-rose-600"
      >
        <SettingRow
          icon={Trash2}
          title="Delete Account"
          description="Permanently delete your account and all associated data. This action cannot be undone."
          iconColor="text-red-500"
          iconBg="bg-red-500/10"
        >
          <Button
            variant="outline"
            className="text-red-500 hover:text-red-600 border-red-500/30 hover:border-red-500/50 hover:bg-red-500/5 rounded-xl"
            onClick={() => {
              toast({
                title: "Contact Support",
                description: "Please contact support to delete your account.",
              })
            }}
          >
            Delete Account
          </Button>
        </SettingRow>
      </SectionCard>
    </div>
  )

  const renderModelsSection = () => (
    <div className="space-y-6">
      {/* Ollama Connection Status */}
      <div className="rounded-2xl border border-border/40 bg-gradient-to-r from-blue-500/5 via-card to-card p-6">
        <div className="flex items-center gap-5">
          <div className="p-4 rounded-xl bg-blue-500/10 ring-4 ring-blue-500/5">
            <Server className="h-6 w-6 text-blue-500" />
          </div>
          <div className="flex-1">
            <p className="font-semibold text-foreground">Local Ollama Server</p>
            <p className="text-sm text-muted-foreground mt-1">
              Embeddings run locally via{' '}
              <code className="text-xs bg-muted/50 px-2 py-1 rounded-lg font-mono border border-border/40">localhost:11434</code>
            </p>
          </div>
          {ollamaStatus === 'checking' ? (
            <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-muted/50 text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm font-semibold">Checking...</span>
            </div>
          ) : ollamaStatus === 'connected' ? (
            <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 text-emerald-600">
              <div className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
              </div>
              <span className="text-sm font-semibold">Connected</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-red-500/10 text-red-600">
              <div className="relative flex h-2.5 w-2.5">
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500"></span>
              </div>
              <span className="text-sm font-semibold">Disconnected</span>
            </div>
          )}
        </div>
      </div>

      {/* Unified Embedding Model Picker - Handles active model display, download & activate */}
      <EmbeddingModelPicker 
        onModelActivated={(modelName, dimension) => {
          // Update local state to match
          setSelectedModel(modelName)
          // Invalidate settings query to refresh
          queryClient.invalidateQueries({ queryKey: ['userSettings'] })
        }}
      />

      {/* How it works info */}
      <div className="rounded-2xl border border-border/40 bg-gradient-to-r from-amber-500/5 via-card to-card p-6">
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-xl bg-amber-500/10">
            <Info className="h-5 w-5 text-amber-500" />
          </div>
          <div>
            <p className="font-semibold text-foreground">How Embedding Models Work</p>
            <ul className="text-sm text-muted-foreground mt-2 space-y-1.5">
              <li className="flex items-start gap-2">
                <span className="text-primary font-bold mt-0.5">1.</span>
                <span><strong>One active model at a time</strong> — Your selected default model is used for all embedding operations.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary font-bold mt-0.5">2.</span>
                <span><strong>Download & Activate</strong> — Downloads a new model and sets it as your default in one click.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary font-bold mt-0.5">3.</span>
                <span><strong>Switching models</strong> — If you switch models, existing dataset embeddings may need to be regenerated.</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )

  const renderContent = () => {
    switch (activeTab) {
      case 'profile':
        return renderProfileSection()
      case 'security':
        return renderSecuritySection()
      case 'llm-providers':
        return <LLMProviderSettings />
      case 'models':
        return renderModelsSection()
      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-background via-background to-muted/30">
      <OnboardingTour tourId="settings" />
      
      <div className="max-w-7xl mx-auto px-6 py-10">
        {/* Page Header */}
        <div className="mb-12">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
            <div>
              <div className="flex items-center gap-4 mb-3">
                <h1 className="text-4xl lg:text-5xl font-bold tracking-tight bg-gradient-to-r from-foreground via-foreground to-foreground/60 bg-clip-text">
                  Settings
                </h1>
                <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                  <div className="relative flex h-2.5 w-2.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                  </div>
                  <span className="text-sm font-semibold text-emerald-600">All Systems Active</span>
                </div>
              </div>
              <p className="text-muted-foreground text-lg">
                Manage your account, security preferences, and AI configurations
              </p>
            </div>

            <Button variant="outline" className="w-full lg:w-auto rounded-xl h-11">
              <RefreshCw className="h-4 w-4 mr-2" />
              Sync Settings
            </Button>
          </div>
        </div>

        {/* Main Layout */}
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar */}
          <aside className="lg:w-80 flex-shrink-0">
            <div className="sticky top-8 space-y-6">
              <nav className="space-y-2 p-3 rounded-2xl border border-border/40 bg-card/60 backdrop-blur-xl shadow-lg shadow-black/5">
                {NAV_ITEMS.map(item => (
                  <NavItem
                    key={item.id}
                    item={item}
                    isActive={activeTab === item.id}
                    onClick={() => setActiveTab(item.id)}
                  />
                ))}
              </nav>

              {/* Help Card */}
              <div className="p-6 rounded-2xl border border-border/40 bg-gradient-to-br from-muted/50 via-card to-muted/30 shadow-lg shadow-black/5">
                <div className="flex items-start gap-4">
                  <div className="p-3 rounded-xl bg-blue-500/10">
                    <Info className="h-5 w-5 text-blue-500" />
                  </div>
                  <div>
                    <p className="font-semibold text-foreground">Need Help?</p>
                    <p className="text-sm text-muted-foreground mt-2 leading-relaxed">
                      Check our documentation or contact support for assistance with settings.
                    </p>
                    <Button variant="link" className="h-auto p-0 mt-3 text-sm text-primary font-semibold">
                      View Documentation →
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </aside>

          {/* Main Content */}
          <main className="flex-1 min-w-0">
            {renderContent()}
          </main>
        </div>
      </div>

      {/* Password Dialog */}
      <Dialog open={isPasswordDialogOpen} onOpenChange={setIsPasswordDialogOpen}>
        <DialogContent className="sm:max-w-md rounded-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3 text-xl">
              <div className="p-2.5 rounded-xl bg-primary/10">
                <Lock className="h-5 w-5 text-primary" />
              </div>
              Change Password
            </DialogTitle>
            <DialogDescription className="pt-2">
              Enter your current password and choose a new secure one.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-5 py-4">
            {passwordError && (
              <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-600 text-sm flex items-center gap-3">
                <XCircle className="h-5 w-5 flex-shrink-0" />
                {passwordError}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="current-password" className="font-semibold">Current Password</Label>
              <div className="relative">
                <Input
                  id="current-password"
                  type={showCurrentPassword ? "text" : "password"}
                  placeholder="Enter current password"
                  value={passwordForm.current_password}
                  onChange={(e) => setPasswordForm(prev => ({ ...prev, current_password: e.target.value }))}
                  className="h-12 pr-12 rounded-xl"
                />
                <button
                  type="button"
                  onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showCurrentPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="new-password" className="font-semibold">New Password</Label>
              <div className="relative">
                <Input
                  id="new-password"
                  type={showNewPassword ? "text" : "password"}
                  placeholder="Enter new password"
                  value={passwordForm.new_password}
                  onChange={(e) => setPasswordForm(prev => ({ ...prev, new_password: e.target.value }))}
                  className="h-12 pr-12 rounded-xl"
                />
                <button
                  type="button"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showNewPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
              <p className="text-xs text-muted-foreground flex items-center gap-1">
                <Info className="h-3 w-3" />
                Minimum 8 characters with uppercase, lowercase, and number
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirm-password" className="font-semibold">Confirm New Password</Label>
              <div className="relative">
                <Input
                  id="confirm-password"
                  type={showConfirmPassword ? "text" : "password"}
                  placeholder="Confirm new password"
                  value={passwordForm.confirm_password}
                  onChange={(e) => setPasswordForm(prev => ({ ...prev, confirm_password: e.target.value }))}
                  className="h-12 pr-12 rounded-xl"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showConfirmPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
            </div>
          </div>

          <DialogFooter className="gap-3 sm:gap-3">
            <Button
              variant="outline"
              onClick={() => {
                setIsPasswordDialogOpen(false)
                setPasswordForm({ current_password: '', new_password: '', confirm_password: '' })
                setPasswordError('')
              }}
              className="rounded-xl"
            >
              Cancel
            </Button>
            <Button onClick={handlePasswordChange} disabled={isPasswordChanging} className="rounded-xl min-w-[140px]">
              {isPasswordChanging ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Changing...
                </>
              ) : (
                'Change Password'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Model Change Confirmation Dialog */}
      <Dialog open={isModelConfirmDialogOpen} onOpenChange={setIsModelConfirmDialogOpen}>
        <DialogContent className="sm:max-w-lg rounded-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3 text-xl">
              <div className="p-2.5 rounded-xl bg-amber-500/10">
                <AlertTriangle className="h-5 w-5 text-amber-500" />
              </div>
              Change Embedding Model
            </DialogTitle>
            <DialogDescription className="pt-2">
              This change may require re-embedding existing datasets.
            </DialogDescription>
          </DialogHeader>

          <div className="py-4 space-y-5">
            {/* Model Comparison */}
            <div className="grid grid-cols-2 gap-4">
              <div className="p-5 rounded-xl bg-muted/30 border border-border/40">
                <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-2">Current Model</p>
                <p className="font-bold text-lg text-foreground">{settings?.default_embedding_model || 'None'}</p>
                <p className="text-xs text-muted-foreground mt-1 font-mono">{settings?.embedding_dimension || 0}D vectors</p>
              </div>
              <div className="p-5 rounded-xl bg-primary/5 border border-primary/30">
                <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-2">New Model</p>
                <p className="font-bold text-lg text-primary">{formatModelName(selectedModel)}</p>
                <p className="text-xs text-primary/70 mt-1 font-mono">{getModelInfo(selectedModel)?.dimension || 0}D vectors</p>
              </div>
            </div>
            
            {/* Impact Assessment */}
            {isLoadingImpact ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground mr-3" />
                <span className="text-muted-foreground">Analyzing impact...</span>
              </div>
            ) : reembeddingImpact?.reembedding_required ? (
              <div className={cn(
                "rounded-xl border p-5",
                reembeddingImpact.impact === 'high' 
                  ? "bg-red-500/10 border-red-500/30" 
                  : reembeddingImpact.impact === 'medium'
                    ? "bg-amber-500/10 border-amber-500/30"
                    : "bg-yellow-500/10 border-yellow-500/30"
              )}>
                <div className="flex items-start gap-4">
                  <div className={cn(
                    "p-2.5 rounded-xl",
                    reembeddingImpact.impact === 'high' ? "bg-red-500/20" : 
                    reembeddingImpact.impact === 'medium' ? "bg-amber-500/20" : "bg-yellow-500/20"
                  )}>
                    <AlertTriangle className={cn(
                      "h-5 w-5",
                      reembeddingImpact.impact === 'high' ? "text-red-500" : 
                      reembeddingImpact.impact === 'medium' ? "text-amber-500" : "text-yellow-500"
                    )} />
                  </div>
                  <div className="flex-1">
                    <p className={cn(
                      "font-bold",
                      reembeddingImpact.impact === 'high' ? "text-red-600 dark:text-red-400" : 
                      reembeddingImpact.impact === 'medium' ? "text-amber-600 dark:text-amber-400" : "text-yellow-600 dark:text-yellow-400"
                    )}>
                      {reembeddingImpact.impact === 'high' ? 'High Impact' : 
                       reembeddingImpact.impact === 'medium' ? 'Medium Impact' : 'Low Impact'}
                    </p>
                    <p className="text-sm text-muted-foreground mt-1">
                      {reembeddingImpact.message}
                    </p>
                    
                    {reembeddingImpact.affected_datasets?.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-border/30">
                        <p className="text-xs font-semibold text-muted-foreground mb-3">Affected Datasets:</p>
                        <ul className="space-y-2">
                          {reembeddingImpact.affected_datasets.slice(0, 5).map((d) => (
                            <li key={d.dataset_id} className="text-xs flex items-center justify-between p-3 rounded-lg bg-muted/30 border border-border/30">
                              <span className="truncate max-w-[200px] font-medium">{d.name}</span>
                              <span className="text-muted-foreground font-mono">{d.embedding_count} vectors</span>
                            </li>
                          ))}
                          {reembeddingImpact.affected_datasets.length > 5 && (
                            <li className="text-xs text-muted-foreground text-center py-2">
                              +{reembeddingImpact.affected_datasets.length - 5} more datasets...
                            </li>
                          )}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : reembeddingImpact?.impact === 'none' ? (
              <div className="rounded-xl border bg-emerald-500/10 border-emerald-500/30 p-5">
                <div className="flex items-center gap-4">
                  <div className="p-2.5 rounded-xl bg-emerald-500/20">
                    <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                  </div>
                  <p className="text-sm text-emerald-600 dark:text-emerald-400 font-semibold">
                    No existing embeddings will be affected.
                  </p>
                </div>
              </div>
            ) : null}
            
            <p className="text-xs text-muted-foreground pt-2 flex items-start gap-2">
              <Info className="h-3.5 w-3.5 mt-0.5 flex-shrink-0" />
              <span>Vectors from different models occupy different vector spaces and cannot be compared directly.</span>
            </p>
          </div>

          <DialogFooter className="gap-3 sm:gap-3">
            <Button
              variant="outline"
              onClick={() => {
                setIsModelConfirmDialogOpen(false)
                setReembeddingImpact(null)
              }}
              className="rounded-xl"
            >
              Cancel
            </Button>
            <Button
              onClick={handleConfirmModelChange}
              disabled={updateSettingsMutation.isPending}
              variant={reembeddingImpact?.impact === 'high' ? 'destructive' : 'default'}
              className="rounded-xl min-w-[140px]"
            >
              {updateSettingsMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                'Confirm Change'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
