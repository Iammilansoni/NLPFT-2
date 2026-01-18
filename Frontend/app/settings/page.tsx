"use client"

import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  User,
  Key,
  Cpu,
  Loader2,
  Check,
  AlertTriangle,
  Shield,
  Settings,
  ChevronRight,
  Lock,
  Trash2,
  Mail,
  UserCircle,
  Fingerprint,
  Zap,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from '@/hooks/use-toast'
import { cn } from '@/lib/utils'
import { apiClient } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'
import authService from '@/lib/auth'
import { EMBEDDING_MODELS, DEFAULT_EMBEDDING_MODEL, type EmbeddingModelOption } from '@/lib/constants/embedding-models'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { OnboardingTour } from '@/components/onboarding/OnboardingTour'

// ============================================================================
// NAVIGATION ITEMS
// ============================================================================

const NAV_ITEMS = [
  { id: 'profile', label: 'Profile', icon: UserCircle, description: 'Personal information' },
  { id: 'security', label: 'Security', icon: Shield, description: 'Password & sessions' },
  { id: 'models', label: 'Models', icon: Cpu, description: 'Embedding configuration' },
  { id: 'api-keys', label: 'API Keys', icon: Key, description: 'Programmatic access' },
] as const

type TabValue = typeof NAV_ITEMS[number]['id']

// ============================================================================
// ENTERPRISE MODEL CARD
// ============================================================================

interface ModelCardProps {
  model: EmbeddingModelOption
  isSelected: boolean
  isCurrentlyActive: boolean
  onSelect: () => void
}

const ModelCard = ({ model, isSelected, isCurrentlyActive, onSelect }: ModelCardProps) => {
  return (
    <button
      onClick={onSelect}
      className={cn(
        "w-full text-left rounded-xl border p-5",
        "bg-card/50 backdrop-blur-sm",
        "transition-all duration-300 ease-out",
        "hover:shadow-md hover:border-border",
        "active:scale-[0.99]",
        isSelected
          ? "border-primary/50 bg-primary/5 ring-1 ring-primary/20"
          : "border-border/60"
      )}
    >
      {/* Header Row */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-semibold text-foreground">
              {model.label}
            </h3>
            <span className="text-xs font-mono text-muted-foreground bg-muted/60 px-2 py-0.5 rounded-full">
              {model.dimension}D
            </span>
            {model.recommended && (
              <span className="text-xs font-medium text-primary bg-primary/10 px-2 py-0.5 rounded-full">
                ★ Recommended
              </span>
            )}
            {isCurrentlyActive && !isSelected && (
              <span className="text-xs text-emerald-600 bg-emerald-500/10 px-2 py-0.5 rounded-full">
                Active
              </span>
            )}
          </div>
          <p className="text-sm text-muted-foreground mt-1.5 leading-relaxed">
            {model.tagline.replace(/^[^\s]+\s/, '')}
          </p>
        </div>

        {/* Selection Indicator */}
        <div className={cn(
          "flex-shrink-0 w-6 h-6 rounded-full border-2 flex items-center justify-center",
          "transition-all duration-200",
          isSelected
            ? "border-primary bg-primary"
            : "border-muted-foreground/30"
        )}>
          {isSelected && <Check className="h-3.5 w-3.5 text-primary-foreground" strokeWidth={3} />}
        </div>
      </div>

      {/* Specs Row */}
      <div className="flex flex-wrap gap-4 mt-4 pt-4 border-t border-border/40">
        {[
          { label: 'Speed', value: model.speed === 'fast' ? 'Fast' : model.speed === 'moderate' ? 'Moderate' : 'Thorough' },
          { label: 'Accuracy', value: model.accuracy === 'superior' ? 'Superior' : model.accuracy === 'excellent' ? 'Excellent' : 'Good' },
          { label: 'Context', value: model.contextLength.replace(' tokens', '') },
          { label: 'Params', value: model.parameters.replace('~', '').replace(' Million', 'M') },
        ].map((spec) => (
          <div key={spec.label} className="text-xs">
            <span className="text-muted-foreground">{spec.label}: </span>
            <span className="text-foreground font-medium">{spec.value}</span>
          </div>
        ))}
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
        "w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left",
        "transition-all duration-200",
        isActive
          ? "bg-primary/10 text-primary border border-primary/20"
          : "hover:bg-muted/50 text-muted-foreground hover:text-foreground"
      )}
    >
      <div className={cn(
        "p-2 rounded-lg transition-colors",
        isActive ? "bg-primary/10" : "bg-muted/50"
      )}>
        <Icon className="h-4 w-4" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-medium text-sm">{item.label}</p>
        <p className="text-xs text-muted-foreground truncate">{item.description}</p>
      </div>
      <ChevronRight className={cn(
        "h-4 w-4 transition-transform",
        isActive ? "text-primary" : "text-muted-foreground/50"
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

  // Model change confirmation dialog state
  const [isModelConfirmDialogOpen, setIsModelConfirmDialogOpen] = useState(false)

  // Update form when user loads
  useEffect(() => {
    if (user) {
      setProfileForm({
        username: user.username || '',
        email: user.email || '',
      })
    }
  }, [user])

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
        title: "Password Changed",
        description: "Your password has been updated successfully.",
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

  // Update selected model when settings load
  useEffect(() => {
    if (settings?.default_embedding_model) {
      setSelectedModel(settings.default_embedding_model)
    } else {
      setSelectedModel(DEFAULT_EMBEDDING_MODEL)
    }
  }, [settings])

  // Mutation to update settings
  const updateSettingsMutation = useMutation({
    mutationFn: (data: { default_embedding_model?: string; embedding_dimension?: number }) =>
      apiClient.updateUserSettings(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['userSettings'] })
      toast({
        title: "Settings Saved",
        description: `Default model updated to ${EMBEDDING_MODELS.find(m => m.value === selectedModel)?.label}`,
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

  const handleSaveModel = () => {
    const model = EMBEDDING_MODELS.find(m => m.value === selectedModel)
    if (!model) return

    if (settings?.default_embedding_model && settings.default_embedding_model !== selectedModel) {
      setIsModelConfirmDialogOpen(true)
    } else {
      updateSettingsMutation.mutate({
        default_embedding_model: selectedModel,
        embedding_dimension: model.dimension
      })
    }
  }

  const handleConfirmModelChange = () => {
    const model = EMBEDDING_MODELS.find(m => m.value === selectedModel)
    if (model) {
      updateSettingsMutation.mutate({
        default_embedding_model: selectedModel,
        embedding_dimension: model.dimension
      })
    }
    setIsModelConfirmDialogOpen(false)
  }

  const hasModelChanged = settings?.default_embedding_model !== selectedModel

  // ============================================================================
  // RENDER SECTIONS
  // ============================================================================

  const renderProfileSection = () => (
    <div className="space-y-6">
      {/* User Avatar Card */}
      <div className="relative overflow-hidden rounded-2xl border border-border/60 bg-card/50 backdrop-blur-sm">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-transparent" />
        <div className="relative p-6">
          {authLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : user ? (
            <div className="flex items-center gap-6">
              <div className="h-20 w-20 rounded-2xl bg-gradient-to-br from-primary to-primary/70 flex items-center justify-center text-3xl font-bold text-primary-foreground shadow-lg">
                {user.username ? user.username.charAt(0).toUpperCase() : user.email.charAt(0).toUpperCase()}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-3">
                  <h2 className="text-2xl font-bold text-foreground">{user.username || 'User'}</h2>
                  {user.is_expert && (
                    <span className="text-xs font-semibold text-amber-600 bg-amber-500/10 px-2.5 py-1 rounded-full border border-amber-500/20">
                      Expert
                    </span>
                  )}
                </div>
                <p className="text-muted-foreground mt-1 flex items-center gap-2">
                  <Mail className="h-4 w-4" />
                  {user.email}
                </p>
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <User className="h-12 w-12 mx-auto mb-3 opacity-40" />
              <p className="text-sm">Please log in to view your profile</p>
            </div>
          )}
        </div>
      </div>

      {/* Profile Form */}
      {user && (
        <div className="rounded-2xl border border-border/60 bg-card/50 backdrop-blur-sm p-6 space-y-5">
          <h3 className="font-semibold text-foreground flex items-center gap-2">
            <UserCircle className="h-5 w-5 text-primary" />
            Account Information
          </h3>

          <div className="grid gap-5">
            <div className="space-y-2">
              <Label htmlFor="username" className="text-sm font-medium text-foreground">
                Username
              </Label>
              <Input
                id="username"
                value={profileForm.username}
                onChange={(e) => setProfileForm(prev => ({ ...prev, username: e.target.value }))}
                placeholder="Your username"
                className="h-11 bg-background/50 border-border/60 focus:border-primary/50 transition-colors"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email" className="text-sm font-medium text-foreground">
                Email Address
              </Label>
              <Input
                id="email"
                type="email"
                value={profileForm.email}
                disabled
                className="h-11 bg-muted/50 cursor-not-allowed"
              />
              <p className="text-xs text-muted-foreground">Email cannot be changed</p>
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium text-foreground">User ID</Label>
              <Input
                value={user.user_id}
                disabled
                className="h-11 bg-muted/50 cursor-not-allowed font-mono text-xs"
              />
            </div>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-border/40">
            <p className="text-sm text-muted-foreground">
              {profileForm.username !== user.username ? '● Unsaved changes' : '✓ Up to date'}
            </p>
            <Button
              disabled={profileForm.username === user.username || isProfileSaving}
              onClick={() => {
                toast({
                  title: "Coming Soon",
                  description: "Profile update functionality will be available soon.",
                })
              }}
              className="transition-all duration-200 active:scale-95"
            >
              {isProfileSaving ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                'Save Changes'
              )}
            </Button>
          </div>
        </div>
      )}
    </div>
  )

  const renderSecuritySection = () => (
    <div className="space-y-6">
      {/* Security Overview */}
      <div className="rounded-2xl border border-border/60 bg-card/50 backdrop-blur-sm overflow-hidden">
        <div className="p-6 border-b border-border/40">
          <h3 className="font-semibold text-foreground flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary" />
            Security Settings
          </h3>
          <p className="text-sm text-muted-foreground mt-1">Manage your account security preferences</p>
        </div>

        <div className="divide-y divide-border/40">
          {/* Password */}
          <div className="flex items-center justify-between p-5 hover:bg-muted/30 transition-colors">
            <div className="flex items-center gap-4">
              <div className="p-2.5 rounded-xl bg-muted/50">
                <Lock className="h-5 w-5 text-muted-foreground" />
              </div>
              <div>
                <p className="font-medium text-foreground">Password</p>
                <p className="text-sm text-muted-foreground">Last changed: Never</p>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsPasswordDialogOpen(true)}
              className="transition-all duration-200 active:scale-95"
            >
              Change
            </Button>
          </div>

          {/* Two-Factor */}
          <div className="flex items-center justify-between p-5 hover:bg-muted/30 transition-colors">
            <div className="flex items-center gap-4">
              <div className="p-2.5 rounded-xl bg-muted/50">
                <Fingerprint className="h-5 w-5 text-muted-foreground" />
              </div>
              <div>
                <p className="font-medium text-foreground">Two-Factor Authentication</p>
                <p className="text-sm text-muted-foreground">Add an extra layer of security</p>
              </div>
            </div>
            <span className="text-xs font-medium text-muted-foreground bg-muted/50 px-3 py-1.5 rounded-full">
              Coming Soon
            </span>
          </div>

          {/* Delete Account */}
          <div className="flex items-center justify-between p-5 hover:bg-muted/30 transition-colors">
            <div className="flex items-center gap-4">
              <div className="p-2.5 rounded-xl bg-destructive/10">
                <Trash2 className="h-5 w-5 text-destructive" />
              </div>
              <div>
                <p className="font-medium text-foreground">Delete Account</p>
                <p className="text-sm text-muted-foreground">Permanently remove your account and data</p>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                toast({
                  title: "Contact Support",
                  description: "Please contact support to delete your account.",
                })
              }}
              className="text-destructive hover:text-destructive border-destructive/30 hover:border-destructive/50 hover:bg-destructive/5 transition-all duration-200 active:scale-95"
            >
              Delete
            </Button>
          </div>
        </div>
      </div>
    </div>
  )

  const renderModelsSection = () => (
    <div className="space-y-6">
      {/* Current Model Banner */}
      {settings?.default_embedding_model && (
        <div className="rounded-2xl border border-primary/20 bg-primary/5 p-5">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-primary/10">
              <Zap className="h-6 w-6 text-primary" />
            </div>
            <div className="flex-1">
              <p className="text-sm text-muted-foreground">Current Active Model</p>
              <p className="text-lg font-bold text-foreground">
                {EMBEDDING_MODELS.find(m => m.value === settings.default_embedding_model)?.label || settings.default_embedding_model}
              </p>
            </div>
            <span className="text-sm font-mono text-muted-foreground bg-muted/50 px-3 py-1.5 rounded-full">
              {settings.embedding_dimension}D vectors
            </span>
          </div>
        </div>
      )}

      {/* Ollama Info */}
      <div className="rounded-xl border border-border/60 bg-muted/30 p-4">
        <p className="text-sm text-muted-foreground">
          Embeddings run locally via Ollama at{' '}
          <code className="text-xs bg-muted px-1.5 py-0.5 rounded font-mono">localhost:11434</code>.
          Ensure Ollama is running before generating embeddings.
        </p>
      </div>

      {/* Model Selection */}
      <div className="space-y-4">
        <h3 className="font-semibold text-foreground" data-tour="model-select">Select Embedding Model</h3>

        {settingsLoading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="space-y-3">
            {EMBEDDING_MODELS.map((model) => (
              <ModelCard
                key={model.value}
                model={model}
                isSelected={selectedModel === model.value}
                isCurrentlyActive={settings?.default_embedding_model === model.value}
                onSelect={() => setSelectedModel(model.value)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Change Notice */}
      {hasModelChanged && settings?.default_embedding_model && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-amber-700 dark:text-amber-400">
              Model change detected
            </p>
            <p className="text-sm text-amber-600/80 dark:text-amber-400/80 mt-1">
              Changing from <strong>{settings.default_embedding_model}</strong> to <strong>{selectedModel}</strong>.
              Existing datasets will need re-embedding.
            </p>
          </div>
        </div>
      )}

      {/* Save Actions */}
      <div className="flex items-center justify-between pt-4 border-t border-border/40">
        <p className="text-sm text-muted-foreground">
          {hasModelChanged ? '● Unsaved changes' : settings?.default_embedding_model ? '✓ Saved' : ''}
        </p>
        <Button
          onClick={handleSaveModel}
          disabled={updateSettingsMutation.isPending || !hasModelChanged}
          className="transition-all duration-200 active:scale-95"
          data-tour="save-settings"
        >
          {updateSettingsMutation.isPending ? 'Saving...' : 'Save Model'}
        </Button>
      </div>
    </div>
  )

  const renderApiKeysSection = () => (
    <div className="space-y-6">
      <div className="rounded-2xl border border-border/60 bg-card/50 backdrop-blur-sm p-12 text-center">
        <div className="mx-auto w-16 h-16 rounded-2xl bg-muted/50 flex items-center justify-center mb-4">
          <Key className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="font-semibold text-foreground mb-2">API Keys Not Available</h3>
        <p className="text-sm text-muted-foreground max-w-sm mx-auto">
          Programmatic API access is not currently enabled for your account.
          Contact your administrator for API access.
        </p>
        <Button
          variant="outline"
          className="mt-6"
          onClick={() => {
            toast({
              title: "Contact Support",
              description: "Please contact support for API key access.",
            })
          }}
        >
          Request Access
        </Button>
      </div>
    </div>
  )

  const renderContent = () => {
    switch (activeTab) {
      case 'profile':
        return renderProfileSection()
      case 'security':
        return renderSecuritySection()
      case 'models':
        return renderModelsSection()
      case 'api-keys':
        return renderApiKeysSection()
      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <OnboardingTour tourId="settings" />
      <div className="max-w-6xl mx-auto p-6 md:p-8">
        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-6 mb-8 border-b border-border/40">
          <div className="space-y-1">
            <div className="flex items-center gap-4">
              <h1 className="text-4xl font-bold tracking-tight text-foreground">
                Settings
              </h1>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-background/50 border border-border/40 backdrop-blur-sm">
                <div className="relative flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                </div>
                <span className="text-sm font-medium text-muted-foreground">
                  Account Active
                </span>
              </div>
            </div>
            <p className="text-base text-muted-foreground/90 font-medium">
              Manage your profile, security, and embedding preferences
            </p>
          </div>
        </div>

        {/* Two Column Layout */}
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar Navigation */}
          <aside className="lg:w-72 flex-shrink-0">
            <nav className="space-y-2 sticky top-8">
              {NAV_ITEMS.map(item => (
                <NavItem
                  key={item.id}
                  item={item}
                  isActive={activeTab === item.id}
                  onClick={() => setActiveTab(item.id)}
                />
              ))}
            </nav>
          </aside>

          {/* Main Content */}
          <main className="flex-1 min-w-0">
            {renderContent()}
          </main>
        </div>
      </div>

      {/* Password Dialog */}
      <Dialog open={isPasswordDialogOpen} onOpenChange={setIsPasswordDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Change Password</DialogTitle>
            <DialogDescription>
              Enter your current password and choose a new one.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {passwordError && (
              <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 flex-shrink-0" />
                {passwordError}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="current-password">Current Password</Label>
              <Input
                id="current-password"
                type="password"
                placeholder="Enter current password"
                value={passwordForm.current_password}
                onChange={(e) => setPasswordForm(prev => ({ ...prev, current_password: e.target.value }))}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="new-password">New Password</Label>
              <Input
                id="new-password"
                type="password"
                placeholder="Enter new password"
                value={passwordForm.new_password}
                onChange={(e) => setPasswordForm(prev => ({ ...prev, new_password: e.target.value }))}
              />
              <p className="text-xs text-muted-foreground">
                Min 8 characters with uppercase, lowercase, and number
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirm-password">Confirm New Password</Label>
              <Input
                id="confirm-password"
                type="password"
                placeholder="Confirm new password"
                value={passwordForm.confirm_password}
                onChange={(e) => setPasswordForm(prev => ({ ...prev, confirm_password: e.target.value }))}
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIsPasswordDialogOpen(false)
                setPasswordForm({ current_password: '', new_password: '', confirm_password: '' })
                setPasswordError('')
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={handlePasswordChange}
              disabled={isPasswordChanging}
            >
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
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Change Embedding Model</DialogTitle>
            <DialogDescription>
              Existing datasets will require re-embedding with the new model.
            </DialogDescription>
          </DialogHeader>

          <div className="py-4 space-y-4 text-sm">
            <div className="grid grid-cols-2 gap-6">
              <div className="p-4 rounded-xl bg-muted/30 border border-border/60">
                <p className="text-muted-foreground mb-1 text-xs uppercase tracking-wider">Current</p>
                <p className="font-semibold text-foreground">{settings?.default_embedding_model || 'None'}</p>
              </div>
              <div className="p-4 rounded-xl bg-primary/5 border border-primary/20">
                <p className="text-muted-foreground mb-1 text-xs uppercase tracking-wider">New</p>
                <p className="font-semibold text-primary">{selectedModel}</p>
              </div>
            </div>
            <p className="text-xs text-muted-foreground pt-3 border-t border-border/40">
              Vectors from different models are incompatible. You will need to re-embed datasets to use the new model for search.
            </p>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsModelConfirmDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleConfirmModelChange}
              disabled={updateSettingsMutation.isPending}
            >
              {updateSettingsMutation.isPending ? 'Saving...' : 'Confirm Change'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
