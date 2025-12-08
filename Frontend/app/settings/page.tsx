"use client"

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  User, 
  Building2, 
  Key, 
  Cpu, 
  Zap,
  Rocket,
  Target,
  Loader2,
  Check,
  AlertTriangle,
  Info,
  Sparkles,
  Clock,
  Brain,
  Gauge,
  ChevronRight,
  Terminal
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { toast } from '@/hooks/use-toast'
import { cn } from '@/lib/utils'
import { apiClient } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'
import authService from '@/lib/auth'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

// Embedding Model Data (matches backend models_config.py)
const EMBEDDING_MODELS = [
  {
    id: "all-minilm",
    name: "All-MiniLM",
    dimension: 384,
    parameters: "~22 Million",
    contextLength: "256-512 tokens",
    speed: "fast",
    accuracy: "good",
    color: "blue",
    icon: Zap,
    tagline: "⚡ Super-Fast Lightweight Embedding Model",
    bestFor: [
      "Real-time applications",
      "Low-latency search",
      "Massive datasets",
      "High-speed indexing"
    ],
    whyChoose: "Perfect for speed-focused scenarios and handling millions of records with minimal compute cost.",
    pullCmd: "ollama pull all-minilm",
    recommended: false
  },
  {
    id: "nomic-embed-text",
    name: "Nomic-Embed-Text",
    dimension: 768,
    parameters: "~137 Million",
    contextLength: "8192 tokens",
    speed: "fast",
    accuracy: "excellent",
    color: "green",
    icon: Rocket,
    tagline: "🚀 High-Quality, Balanced Default Embedding Model",
    bestFor: [
      "General semantic search",
      "RAG applications",
      "High-quality embeddings",
      "Most production workloads"
    ],
    whyChoose: "The recommended default model offering the best balance between speed, context, and accuracy.",
    pullCmd: "ollama pull nomic-embed-text",
    recommended: true
  },
  {
    id: "mxbai-embed-large",
    name: "MXBai-Embed-Large",
    dimension: 1024,
    parameters: "~335 Million",
    contextLength: "512 tokens",
    speed: "moderate",
    accuracy: "superior",
    color: "red",
    icon: Target,
    tagline: "🎯 High-Precision, Heavy-Duty Embedding Model",
    bestFor: [
      "Precision-critical search",
      "Legal, medical, enterprise retrieval",
      "Engineering documents",
      "When accuracy matters most"
    ],
    whyChoose: "Ideal for scenarios requiring maximum semantic precision and deep document understanding.",
    pullCmd: "ollama pull mxbai-embed-large",
    recommended: false
  }
]

// Speed badge component
const SpeedBadge = ({ speed }: { speed: string }) => {
  const config = {
    fast: { icon: "⚡", label: "Extremely Fast", class: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400" },
    moderate: { icon: "🐢", label: "Moderate", class: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400" },
    slow: { icon: "🐌", label: "Slow", class: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400" }
  }
  const { icon, label, class: className } = config[speed as keyof typeof config] || config.moderate
  return (
    <span className={cn("inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium", className)}>
      {icon} {label}
    </span>
  )
}

// Accuracy badge component
const AccuracyBadge = ({ accuracy }: { accuracy: string }) => {
  const config = {
    good: { label: "Good", class: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400" },
    excellent: { label: "Excellent", class: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400" },
    superior: { label: "Superior (Best)", class: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400" }
  }
  const { label, class: className } = config[accuracy as keyof typeof config] || config.good
  return (
    <span className={cn("inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium", className)}>
      {label}
    </span>
  )
}

// Model Card Component
const EmbeddingModelCard = ({ 
  model, 
  isSelected, 
  currentModel,
  onSelect 
}: { 
  model: typeof EMBEDDING_MODELS[0]
  isSelected: boolean
  currentModel?: string
  onSelect: () => void 
}) => {
  const Icon = model.icon
  const isCurrentlyActive = currentModel === model.id
  
  const colorClasses = {
    blue: {
      border: "border-blue-500",
      bg: "bg-blue-500/10",
      text: "text-blue-600 dark:text-blue-400",
      glow: "shadow-blue-500/20"
    },
    green: {
      border: "border-green-500",
      bg: "bg-green-500/10", 
      text: "text-green-600 dark:text-green-400",
      glow: "shadow-green-500/20"
    },
    red: {
      border: "border-red-500",
      bg: "bg-red-500/10",
      text: "text-red-600 dark:text-red-400",
      glow: "shadow-red-500/20"
    }
  }
  
  const colors = colorClasses[model.color as keyof typeof colorClasses] || colorClasses.blue

  return (
    <motion.div
      whileHover={{ scale: 1.01, y: -2 }}
      whileTap={{ scale: 0.99 }}
      transition={{ duration: 0.2 }}
    >
      <button
        onClick={onSelect}
        className={cn(
          "relative w-full text-left rounded-xl border-2 p-5 transition-all duration-300",
          "hover:shadow-lg",
          isSelected 
            ? cn(colors.border, colors.bg, "shadow-lg", colors.glow)
            : "border-border bg-card hover:border-muted-foreground/30 hover:bg-accent/50"
        )}
      >
        {/* Recommended Badge */}
        {model.recommended && (
          <div className="absolute -top-3 left-4">
            <Badge className="bg-gradient-to-r from-green-500 to-emerald-500 text-white shadow-lg">
              <Sparkles className="h-3 w-3 mr-1" />
              Recommended
            </Badge>
          </div>
        )}
        
        {/* Active Badge */}
        {isCurrentlyActive && !isSelected && (
          <div className="absolute -top-3 right-4">
            <Badge variant="outline" className="border-primary text-primary bg-background">
              Currently Active
            </Badge>
          </div>
        )}
        
        {/* Selected Indicator */}
        {isSelected && (
          <div className="absolute -top-3 right-4">
            <Badge className="bg-primary text-primary-foreground shadow-lg">
              <Check className="h-3 w-3 mr-1" />
              Selected
            </Badge>
          </div>
        )}

        {/* Header */}
        <div className="flex items-start gap-4 mb-4">
          <div className={cn(
            "flex-shrink-0 p-3 rounded-xl",
            isSelected ? colors.bg : "bg-muted"
          )}>
            <Icon className={cn("h-6 w-6", isSelected ? colors.text : "text-muted-foreground")} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-bold text-lg">{model.name}</h3>
              <Badge variant="secondary" className="font-mono text-xs">
                {model.dimension}D
              </Badge>
            </div>
            <p className={cn(
              "text-sm font-medium",
              isSelected ? colors.text : "text-muted-foreground"
            )}>
              {model.tagline}
            </p>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="flex items-center gap-2 text-sm">
            <Brain className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">Parameters:</span>
            <span className="font-medium">{model.parameters}</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">Context:</span>
            <span className="font-medium">{model.contextLength}</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Gauge className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">Speed:</span>
            <SpeedBadge speed={model.speed} />
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Target className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">Accuracy:</span>
            <AccuracyBadge accuracy={model.accuracy} />
          </div>
        </div>

        {/* Best For Section */}
        <div className="mb-4">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
            Best Use Cases
          </p>
          <div className="flex flex-wrap gap-1.5">
            {model.bestFor.map((useCase, idx) => (
              <span 
                key={idx}
                className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-muted text-xs"
              >
                <ChevronRight className="h-3 w-3" />
                {useCase}
              </span>
            ))}
          </div>
        </div>

        {/* Why Choose */}
        <p className="text-sm text-muted-foreground italic mb-4">
          "{model.whyChoose}"
        </p>

        {/* Install Command */}
        <div className="flex items-center gap-2 p-2 rounded-lg bg-muted/50 border border-border">
          <Terminal className="h-4 w-4 text-muted-foreground" />
          <code className="text-xs font-mono text-muted-foreground flex-1 truncate">
            {model.pullCmd}
          </code>
        </div>
      </button>
    </motion.div>
  )
}

// Settings Page
export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('profile')
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
    
    // Validate
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
    
    // Check password strength
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
        title: "✅ Password Changed",
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
      setSelectedModel('nomic-embed-text') // Default
    }
  }, [settings])

  // Mutation to update settings
  const updateSettingsMutation = useMutation({
    mutationFn: (data: { default_embedding_model?: string; embedding_dimension?: number }) => 
      apiClient.updateUserSettings(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['userSettings'] })
      toast({
        title: "✅ Embedding Model Updated",
        description: `Your default model is now ${EMBEDDING_MODELS.find(m => m.id === selectedModel)?.name}`,
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
    const model = EMBEDDING_MODELS.find(m => m.id === selectedModel)
    if (model) {
      updateSettingsMutation.mutate({
        default_embedding_model: selectedModel,
        embedding_dimension: model.dimension
      })
    }
  }

  const hasModelChanged = settings?.default_embedding_model !== selectedModel

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="mb-8"
      >
        <h1 className="text-4xl font-bold font-heading mb-2">Settings</h1>
        <p className="text-muted-foreground">
          Configure your embedding models, account, and integrations
        </p>
      </motion.div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="profile" className="flex items-center gap-2">
            <User className="h-4 w-4" />
            <span className="hidden sm:inline">Profile</span>
          </TabsTrigger>
          <TabsTrigger value="models" className="flex items-center gap-2">
            <Cpu className="h-4 w-4" />
            <span className="hidden sm:inline">AI Models</span>
          </TabsTrigger>
          <TabsTrigger value="organization" className="flex items-center gap-2">
            <Building2 className="h-4 w-4" />
            <span className="hidden sm:inline">Organization</span>
          </TabsTrigger>
          <TabsTrigger value="api-keys" className="flex items-center gap-2">
            <Key className="h-4 w-4" />
            <span className="hidden sm:inline">API Keys</span>
          </TabsTrigger>
        </TabsList>

        {/* Profile Tab */}
        <TabsContent value="profile" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Personal Information</CardTitle>
              <CardDescription>View and manage your profile details</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {authLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
              ) : user ? (
                <>
                  {/* Profile Header */}
                  <div className="flex items-center gap-4 p-4 rounded-xl bg-gradient-to-r from-primary/10 via-purple-500/10 to-pink-500/10 border">
                    <div className="relative">
                      <div className="h-16 w-16 rounded-xl bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white text-xl font-bold shadow-lg">
                        {user.username ? user.username.charAt(0).toUpperCase() : user.email.charAt(0).toUpperCase()}
                      </div>
                      <div className="absolute -bottom-1 -right-1 h-5 w-5 bg-emerald-500 rounded-full border-2 border-background flex items-center justify-center">
                        <Check className="h-3 w-3 text-white" />
                      </div>
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold">{user.username || 'User'}</h3>
                      <p className="text-sm text-muted-foreground">{user.email}</p>
                      <div className="flex items-center gap-2 mt-1">
                        {user.is_expert && (
                          <Badge className="bg-purple-500/20 text-purple-700 dark:text-purple-300 border-purple-500/30">
                            <Sparkles className="h-3 w-3 mr-1" />
                            Expert
                          </Badge>
                        )}
                        <Badge variant="outline" className="text-xs">
                          <Clock className="h-3 w-3 mr-1" />
                          Joined {new Date(user.created_at).toLocaleDateString()}
                        </Badge>
                      </div>
                    </div>
                  </div>

                  {/* Account Details */}
                  <div className="grid gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="username">Username</Label>
                      <Input 
                        id="username" 
                        value={profileForm.username}
                        onChange={(e) => setProfileForm(prev => ({ ...prev, username: e.target.value }))}
                        placeholder="Your username"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="email">Email Address</Label>
                      <Input 
                        id="email" 
                        type="email" 
                        value={profileForm.email}
                        disabled
                        className="bg-muted cursor-not-allowed"
                      />
                      <p className="text-xs text-muted-foreground">Email cannot be changed</p>
                    </div>
                    <div className="space-y-2">
                      <Label>User ID</Label>
                      <Input 
                        value={user.user_id}
                        disabled
                        className="bg-muted cursor-not-allowed font-mono text-xs"
                      />
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-4 border-t">
                    <p className="text-sm text-muted-foreground">
                      {profileForm.username !== user.username ? 'You have unsaved changes' : 'Profile is up to date'}
                    </p>
                    <Button 
                      disabled={profileForm.username === user.username || isProfileSaving}
                      onClick={() => {
                        toast({
                          title: "Coming Soon",
                          description: "Profile update functionality will be available soon.",
                        })
                      }}
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
                </>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <User className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Please log in to view your profile</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Security Section */}
          <Card>
            <CardHeader>
              <CardTitle>Security</CardTitle>
              <CardDescription>Manage your account security</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 rounded-lg border bg-muted/30">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-amber-500/20">
                    <Key className="h-5 w-5 text-amber-600" />
                  </div>
                  <div>
                    <p className="font-medium">Change Password</p>
                    <p className="text-sm text-muted-foreground">Update your account password</p>
                  </div>
                </div>
                <Button variant="outline" onClick={() => setIsPasswordDialogOpen(true)}>
                  Change
                </Button>
              </div>
              
              <div className="flex items-center justify-between p-4 rounded-lg border bg-red-500/5 border-red-500/20">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-red-500/20">
                    <AlertTriangle className="h-5 w-5 text-red-600" />
                  </div>
                  <div>
                    <p className="font-medium text-red-600">Delete Account</p>
                    <p className="text-sm text-muted-foreground">Permanently delete your account and data</p>
                  </div>
                </div>
                <Button variant="destructive" size="sm" onClick={() => {
                  toast({
                    title: "Contact Support",
                    description: "Please contact support to delete your account.",
                    variant: "destructive",
                  })
                }}>
                  Delete
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Change Password Dialog */}
          <Dialog open={isPasswordDialogOpen} onOpenChange={setIsPasswordDialogOpen}>
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <Key className="h-5 w-5 text-primary" />
                  Change Password
                </DialogTitle>
                <DialogDescription>
                  Enter your current password and choose a new one.
                </DialogDescription>
              </DialogHeader>
              
              <div className="space-y-4 py-4">
                {passwordError && (
                  <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-600 text-sm flex items-center gap-2">
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
        </TabsContent>

        {/* AI Models Tab */}
        <TabsContent value="models" className="space-y-6">
          {/* Header Card */}
          <Card className="border-2 border-dashed">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500">
                  <Brain className="h-6 w-6 text-white" />
                </div>
                <div>
                  <CardTitle className="text-2xl">Embedding Model Configuration</CardTitle>
                  <CardDescription className="text-base">
                    Select the AI model used for generating vector embeddings
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
          </Card>

          {settingsLoading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <>
              {/* Ollama Status Card */}
              <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/30 dark:to-indigo-950/30 border-blue-200 dark:border-blue-800">
                <CardContent className="p-4">
                  <div className="flex items-start gap-4">
                    <div className="p-2 rounded-lg bg-blue-500/20">
                      <Cpu className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-1">
                        Ollama-Powered Embeddings (CPU-Based)
                      </h3>
                      <p className="text-sm text-blue-700 dark:text-blue-300 mb-2">
                        All embeddings run locally using Ollama at <code className="bg-blue-200/50 dark:bg-blue-800/50 px-1 rounded">http://localhost:11434</code>. 
                        No GPU required. Make sure Ollama is running before generating embeddings.
                      </p>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="border-blue-400 text-blue-700 dark:text-blue-300">
                          <Terminal className="h-3 w-3 mr-1" />
                          ollama serve
                        </Badge>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Current Active Model */}
              {settings?.default_embedding_model && (
                <Card className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-950/30 dark:to-emerald-950/30 border-green-200 dark:border-green-800">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-green-500/20">
                          <Check className="h-5 w-5 text-green-600 dark:text-green-400" />
                        </div>
                        <div>
                          <p className="font-semibold text-green-900 dark:text-green-100">
                            Currently Active: {EMBEDDING_MODELS.find(m => m.id === settings.default_embedding_model)?.name || settings.default_embedding_model}
                          </p>
                          <p className="text-sm text-green-700 dark:text-green-300">
                            {settings.embedding_dimension}D vectors • Used for all new embeddings & searches
                          </p>
                        </div>
                      </div>
                      <Badge className="bg-green-600 text-white">
                        Active
                      </Badge>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Model Selection Cards */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-semibold">Select Embedding Model</h2>
                  <p className="text-sm text-muted-foreground">
                    Higher dimensions = better accuracy, but slower
                  </p>
                </div>
                
                <div className="grid gap-4">
                  {EMBEDDING_MODELS.map((model) => (
                    <EmbeddingModelCard
                      key={model.id}
                      model={model}
                      isSelected={selectedModel === model.id}
                      currentModel={settings?.default_embedding_model}
                      onSelect={() => setSelectedModel(model.id)}
                    />
                  ))}
                </div>
              </div>

              {/* Model Change Warning */}
              <AnimatePresence>
                {hasModelChanged && settings?.default_embedding_model && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                  >
                    <Card className="bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-950/30 dark:to-orange-950/30 border-amber-200 dark:border-amber-800">
                      <CardContent className="p-4">
                        <div className="flex items-start gap-3">
                          <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
                          <div className="space-y-2">
                            <h4 className="font-semibold text-amber-900 dark:text-amber-100">
                              ⚠️ Model Change Detected
                            </h4>
                            <p className="text-sm text-amber-700 dark:text-amber-300">
                              You're changing from <strong>{settings.default_embedding_model}</strong> to <strong>{selectedModel}</strong>.
                              Existing datasets embedded with the old model will show a "Model Mismatch" warning on the Dashboard.
                              You'll need to re-embed datasets to use the new model for search.
                            </p>
                            <div className="flex items-center gap-2 pt-1">
                              <Info className="h-4 w-4 text-amber-600" />
                              <span className="text-xs text-amber-600 dark:text-amber-400">
                                Vectors from different models are incompatible and produce incorrect similarity scores.
                              </span>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* LLM Model (Fixed) */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Sparkles className="h-5 w-5 text-purple-500" />
                    Dataset Generation LLM
                  </CardTitle>
                  <CardDescription>
                    The LLM used for generating test datasets from templates
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-4 p-4 rounded-lg bg-muted/50 border">
                    <div className="p-2 rounded-lg bg-purple-500/20">
                      <Brain className="h-5 w-5 text-purple-600" />
                    </div>
                    <div className="flex-1">
                      <p className="font-semibold">Gemini 2.5 Pro</p>
                      <p className="text-sm text-muted-foreground">
                        Google's latest Gemini 2.5 Pro for high-quality dataset generation
                      </p>
                    </div>
                    <Badge variant="outline">Fixed</Badge>
                  </div>
                </CardContent>
              </Card>

              {/* Save Button */}
              <div className="flex items-center justify-end gap-4 pt-4 border-t">
                {hasModelChanged && (
                  <p className="text-sm text-muted-foreground">
                    Unsaved changes
                  </p>
                )}
                <Button 
                  onClick={handleSaveModel}
                  disabled={updateSettingsMutation.isPending || !hasModelChanged}
                  size="lg"
                  className="min-w-[200px]"
                >
                  {updateSettingsMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Check className="h-4 w-4 mr-2" />
                      Save Embedding Model
                    </>
                  )}
                </Button>
              </div>
            </>
          )}
        </TabsContent>

        {/* Organization Tab */}
        <TabsContent value="organization" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Organization Details</CardTitle>
              <CardDescription>Organization settings and team management</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-center py-12 text-muted-foreground">
                <Building2 className="h-16 w-16 mx-auto mb-4 opacity-30" />
                <h3 className="text-lg font-semibold mb-2">Organization Features Coming Soon</h3>
                <p className="text-sm max-w-md mx-auto">
                  Team collaboration, organization management, and shared workspaces will be available in a future update.
                </p>
                <div className="flex items-center justify-center gap-2 mt-4">
                  <Badge variant="outline">
                    <Clock className="h-3 w-3 mr-1" />
                    In Development
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* API Keys Tab */}
        <TabsContent value="api-keys" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>API Keys</CardTitle>
              <CardDescription>
                API key management is not currently available
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                <Key className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>API key management is not implemented yet.</p>
                <p className="text-sm mt-2">Contact your administrator for API access.</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
