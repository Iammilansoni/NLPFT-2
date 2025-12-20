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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

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
        "w-full text-left rounded-md border p-4",
        "bg-white dark:bg-slate-900",
        "transition-all duration-200 ease-in-out",
        "hover:border-slate-300 dark:hover:border-slate-600",
        "active:scale-[0.99]",
        isSelected
          ? "border-slate-700 dark:border-slate-400 ring-1 ring-slate-700/20 dark:ring-slate-400/20"
          : "border-slate-200/80 dark:border-slate-800"
      )}
    >
      {/* Header Row */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-medium text-slate-900 dark:text-slate-100">
              {model.label}
            </h3>
            <span className="text-xs font-mono text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded">
              {model.dimension}D
            </span>
            {model.recommended && (
              <span className="text-xs font-medium text-slate-600 dark:text-slate-300">
                Recommended
              </span>
            )}
            {isCurrentlyActive && !isSelected && (
              <span className="text-xs text-slate-500">
                Current
              </span>
            )}
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            {model.tagline.replace(/^[^\s]+\s/, '')}
          </p>
        </div>

        {/* Selection Indicator */}
        <div className={cn(
          "flex-shrink-0 w-5 h-5 rounded-full border-2 flex items-center justify-center",
          "transition-all duration-200",
          isSelected
            ? "border-slate-700 dark:border-slate-300 bg-slate-700 dark:bg-slate-300"
            : "border-slate-300 dark:border-slate-600"
        )}>
          {isSelected && <Check className="h-3 w-3 text-white dark:text-slate-900" strokeWidth={3} />}
        </div>
      </div>

      {/* Specs Row */}
      <div className="flex gap-6 mt-3 pt-3 border-t border-slate-100 dark:border-slate-800">
        {[
          { label: 'Speed', value: model.speed === 'fast' ? 'Fast' : model.speed === 'moderate' ? 'Moderate' : 'Thorough' },
          { label: 'Accuracy', value: model.accuracy === 'superior' ? 'Superior' : model.accuracy === 'excellent' ? 'Excellent' : 'Good' },
          { label: 'Context', value: model.contextLength.replace(' tokens', '') },
          { label: 'Params', value: model.parameters.replace('~', '').replace(' Million', 'M') },
        ].map((spec) => (
          <div key={spec.label} className="text-xs">
            <span className="text-slate-400 dark:text-slate-500">{spec.label}:</span>{' '}
            <span className="text-slate-600 dark:text-slate-300 font-medium">{spec.value}</span>
          </div>
        ))}
      </div>
    </button>
  )
}

// ============================================================================
// MAIN SETTINGS PAGE
// ============================================================================

type TabValue = 'profile' | 'models' | 'api-keys'

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

  return (
    <div className="max-w-3xl mx-auto px-6 py-10">
      {/* Page Header */}
      <div className="mb-10">
        <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Settings</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Manage your account and embedding configuration
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as TabValue)} className="space-y-8">
        <TabsList className="grid w-full grid-cols-3 bg-slate-100 dark:bg-slate-800/50 p-1 rounded-md">
          <TabsTrigger
            value="profile"
            className="flex items-center gap-2 text-sm data-[state=active]:bg-white dark:data-[state=active]:bg-slate-900 data-[state=active]:shadow-sm transition-all duration-200"
          >
            <User className="h-4 w-4" />
            <span className="hidden sm:inline">Profile</span>
          </TabsTrigger>
          <TabsTrigger
            value="models"
            className="flex items-center gap-2 text-sm data-[state=active]:bg-white dark:data-[state=active]:bg-slate-900 data-[state=active]:shadow-sm transition-all duration-200"
          >
            <Cpu className="h-4 w-4" />
            <span className="hidden sm:inline">Models</span>
          </TabsTrigger>
          <TabsTrigger
            value="api-keys"
            className="flex items-center gap-2 text-sm data-[state=active]:bg-white dark:data-[state=active]:bg-slate-900 data-[state=active]:shadow-sm transition-all duration-200"
          >
            <Key className="h-4 w-4" />
            <span className="hidden sm:inline">API Keys</span>
          </TabsTrigger>
        </TabsList>

        {/* ============================================================ */}
        {/* PROFILE TAB */}
        {/* ============================================================ */}
        <TabsContent value="profile" className="space-y-8">
          {/* Account Section */}
          <section>
            <div className="mb-4">
              <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Account</h2>
              <p className="text-sm text-slate-500 dark:text-slate-400">Your personal account information</p>
            </div>

            <Card className="border-slate-200/80 dark:border-slate-800 shadow-none">
              <CardContent className="p-6">
                {authLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-5 w-5 animate-spin text-slate-400" />
                  </div>
                ) : user ? (
                  <div className="space-y-6">
                    {/* User Summary */}
                    <div className="flex items-center gap-4 pb-6 border-b border-slate-100 dark:border-slate-800">
                      <div className="h-12 w-12 rounded-md bg-slate-700 flex items-center justify-center text-white font-medium">
                        {user.username ? user.username.charAt(0).toUpperCase() : user.email.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <p className="font-medium text-slate-900 dark:text-slate-100">{user.username || 'User'}</p>
                        <p className="text-sm text-slate-500 dark:text-slate-400">{user.email}</p>
                      </div>
                      {user.is_expert && (
                        <span className="ml-auto text-xs font-medium text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">
                          Expert
                        </span>
                      )}
                    </div>

                    {/* Form Fields */}
                    <div className="grid gap-5">
                      <div className="space-y-2">
                        <Label htmlFor="username" className="text-sm font-medium text-slate-700 dark:text-slate-300">
                          Username
                        </Label>
                        <Input
                          id="username"
                          value={profileForm.username}
                          onChange={(e) => setProfileForm(prev => ({ ...prev, username: e.target.value }))}
                          placeholder="Your username"
                          className="h-10 border-slate-200 dark:border-slate-700 focus:ring-slate-700/20 transition-colors duration-200"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="email" className="text-sm font-medium text-slate-700 dark:text-slate-300">
                          Email Address
                        </Label>
                        <Input
                          id="email"
                          type="email"
                          value={profileForm.email}
                          disabled
                          className="h-10 bg-slate-50 dark:bg-slate-800 cursor-not-allowed"
                        />
                        <p className="text-xs text-slate-400">Email cannot be changed</p>
                      </div>
                      <div className="space-y-2">
                        <Label className="text-sm font-medium text-slate-700 dark:text-slate-300">User ID</Label>
                        <Input
                          value={user.user_id}
                          disabled
                          className="h-10 bg-slate-50 dark:bg-slate-800 cursor-not-allowed font-mono text-xs"
                        />
                      </div>
                    </div>

                    {/* Save Button */}
                    <div className="flex items-center justify-between pt-4 border-t border-slate-100 dark:border-slate-800">
                      <p className="text-sm text-slate-500">
                        {profileForm.username !== user.username ? 'Unsaved changes' : 'Up to date'}
                      </p>
                      <Button
                        disabled={profileForm.username === user.username || isProfileSaving}
                        onClick={() => {
                          toast({
                            title: "Coming Soon",
                            description: "Profile update functionality will be available soon.",
                          })
                        }}
                        className="bg-slate-700 hover:bg-slate-800 text-white transition-all duration-200 active:scale-95"
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
                ) : (
                  <div className="text-center py-10 text-slate-500">
                    <User className="h-10 w-10 mx-auto mb-3 opacity-40" />
                    <p className="text-sm">Please log in to view your profile</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </section>

          {/* Security Section */}
          <section>
            <div className="mb-4">
              <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Security</h2>
              <p className="text-sm text-slate-500 dark:text-slate-400">Manage your account security settings</p>
            </div>

            <Card className="border-slate-200/80 dark:border-slate-800 shadow-none">
              <CardContent className="p-0">
                <div className="flex items-center justify-between p-4 border-b border-slate-100 dark:border-slate-800">
                  <div>
                    <p className="text-sm font-medium text-slate-900 dark:text-slate-100">Password</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">Update your account password</p>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setIsPasswordDialogOpen(true)}
                    className="border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 transition-all duration-200 active:scale-95"
                  >
                    Change
                  </Button>
                </div>

                <div className="flex items-center justify-between p-4">
                  <div>
                    <p className="text-sm font-medium text-slate-900 dark:text-slate-100">Delete Account</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">Permanently remove your account and data</p>
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
                    className="border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-600 transition-all duration-200 active:scale-95"
                  >
                    Delete
                  </Button>
                </div>
              </CardContent>
            </Card>
          </section>

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
                  <div className="p-3 rounded-md bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-sm flex items-center gap-2">
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
                    className="transition-colors duration-200"
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
                    className="transition-colors duration-200"
                  />
                  <p className="text-xs text-slate-500">
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
                    className="transition-colors duration-200"
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
                  className="transition-all duration-200 active:scale-95"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handlePasswordChange}
                  disabled={isPasswordChanging}
                  className="bg-slate-700 hover:bg-slate-800 text-white transition-all duration-200 active:scale-95"
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
                  <div>
                    <p className="text-slate-500 mb-1">Current</p>
                    <p className="font-medium text-slate-900 dark:text-slate-100">{settings?.default_embedding_model || 'None'}</p>
                  </div>
                  <div>
                    <p className="text-slate-500 mb-1">New</p>
                    <p className="font-medium text-slate-900 dark:text-slate-100">{selectedModel}</p>
                  </div>
                </div>
                <p className="text-xs text-slate-500 pt-3 border-t border-slate-100 dark:border-slate-800">
                  Vectors from different models are incompatible. You will need to re-embed datasets to use the new model for search.
                </p>
              </div>

              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setIsModelConfirmDialogOpen(false)}
                  className="transition-all duration-200 active:scale-95"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleConfirmModelChange}
                  disabled={updateSettingsMutation.isPending}
                  className="bg-slate-700 hover:bg-slate-800 text-white transition-all duration-200 active:scale-95"
                >
                  {updateSettingsMutation.isPending ? 'Saving...' : 'Confirm Change'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </TabsContent>

        {/* ============================================================ */}
        {/* MODELS TAB */}
        {/* ============================================================ */}
        <TabsContent value="models" className="space-y-8">
          <section>
            <div className="mb-4">
              <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Embedding Model</h2>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Select the default model used for vector embeddings
              </p>
            </div>

            {settingsLoading ? (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
              </div>
            ) : (
              <div className="space-y-6">
                {/* Status Banner */}
                <div className="p-4 rounded-md border border-slate-200/80 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/30">
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    Embeddings run locally via Ollama at{' '}
                    <code className="text-xs bg-slate-200 dark:bg-slate-700 px-1.5 py-0.5 rounded font-mono">localhost:11434</code>.
                    Ensure Ollama is running before generating embeddings.
                  </p>
                </div>

                {/* Current Model Display */}
                {settings?.default_embedding_model && (
                  <div className="p-4 rounded-md border border-slate-200/80 dark:border-slate-800">
                    <p className="text-sm text-slate-700 dark:text-slate-300">
                      <span className="text-slate-500">Current model:</span>{' '}
                      <span className="font-medium">{EMBEDDING_MODELS.find(m => m.value === settings.default_embedding_model)?.label || settings.default_embedding_model}</span>
                      <span className="text-slate-400 ml-2">· {settings.embedding_dimension}D vectors</span>
                    </p>
                  </div>
                )}

                {/* Model Selection */}
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

                {/* Change Notice */}
                {hasModelChanged && settings?.default_embedding_model && (
                  <div className="p-3 rounded-md border border-amber-200 dark:border-amber-800/50 bg-amber-50 dark:bg-amber-900/20">
                    <p className="text-xs text-amber-700 dark:text-amber-400">
                      Changing from <strong>{settings.default_embedding_model}</strong> to <strong>{selectedModel}</strong>.
                      Existing datasets will need re-embedding.
                    </p>
                  </div>
                )}

                {/* Save Actions */}
                <div className="flex items-center justify-between pt-4 border-t border-slate-100 dark:border-slate-800">
                  <p className="text-sm text-slate-500">
                    {hasModelChanged ? 'Unsaved changes' : settings?.default_embedding_model ? 'Saved' : ''}
                  </p>
                  <Button
                    onClick={handleSaveModel}
                    disabled={updateSettingsMutation.isPending || !hasModelChanged}
                    className="bg-slate-700 hover:bg-slate-800 text-white transition-all duration-200 active:scale-95 disabled:opacity-50"
                  >
                    {updateSettingsMutation.isPending ? 'Saving...' : 'Save Changes'}
                  </Button>
                </div>
              </div>
            )}
          </section>
        </TabsContent>

        {/* ============================================================ */}
        {/* API KEYS TAB */}
        {/* ============================================================ */}
        <TabsContent value="api-keys" className="space-y-8">
          <section>
            <div className="mb-4">
              <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">API Keys</h2>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Manage programmatic access to the API
              </p>
            </div>

            <Card className="border-slate-200/80 dark:border-slate-800 shadow-none">
              <CardContent className="p-0">
                <div className="text-center py-12 text-slate-500">
                  <Key className="h-8 w-8 mx-auto mb-3 opacity-40" />
                  <p className="text-sm font-medium text-slate-700 dark:text-slate-300">API keys not available</p>
                  <p className="text-xs mt-1">Contact your administrator for API access.</p>
                </div>
              </CardContent>
            </Card>
          </section>
        </TabsContent>
      </Tabs>
    </div>
  )
}
