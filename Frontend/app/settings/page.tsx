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
  Boxes,
  Workflow,
  Eye,
  EyeOff,
  Settings2,
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
import { RuntimeInfoPanel } from '@/components/settings/RuntimeInfoPanel'
import { ModelCatalogPanel } from '@/components/settings/ModelCatalogPanel'
import { EmbeddingSettings } from '@/components/settings/EmbeddingSettings'
import { PageHeader } from '@/components/ui/page-header'

// ============================================================================
// NAVIGATION ITEMS
// ============================================================================

const NAV_ITEMS = [
  { id: 'profile', label: 'Profile', icon: UserCircle, description: 'Manage your account information', color: 'from-info to-primary' },
  { id: 'security', label: 'Security', icon: Shield, description: 'Password, 2FA, and sessions', color: 'from-success to-success' },
  { id: 'llm-providers', label: 'AI Providers', icon: Sparkles, description: 'Configure LLM integrations', color: 'from-primary to-brand-2' },
  { id: 'embeddings', label: 'Embedding model', icon: Layers, description: 'How requests become vectors', color: 'from-success to-info' },
  { id: 'catalogue', label: 'Model catalogue', icon: Boxes, description: 'Every model your providers serve', color: 'from-info to-primary' },
  { id: 'models', label: 'Pipeline', icon: Workflow, description: 'How queries are routed', color: 'from-warning to-warning' },
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

  // Security alerts state - initialize from localStorage
  const [securityAlertsEnabled, setSecurityAlertsEnabled] = useState(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('securityAlertsEnabled')
      return stored !== null ? stored === 'true' : true
    }
    return true
  })
  
  // Deep links such as /settings?tab=embeddings open that tab.
  useEffect(() => {
    const tab = new URLSearchParams(window.location.search).get('tab')
    if (tab && NAV_ITEMS.some(item => item.id === tab)) setActiveTab(tab as TabValue)
  }, [])

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
        <div className="absolute bottom-0 left-0 w-[300px] h-[300px] bg-gradient-to-tr from-info/10 via-transparent to-transparent rounded-full blur-3xl translate-y-1/2 -translate-x-1/4" />
        
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
                <div className="absolute -bottom-2 -right-2 p-2.5 bg-success rounded-xl shadow-lg shadow-success/30 ring-4 ring-card">
                  <CheckCircle2 className="h-4 w-4 text-white" />
                </div>
              </div>

              {/* User Info */}
              <div className="flex-1">
                <div className="flex items-center gap-3 flex-wrap">
                  <h2 className="text-4xl font-bold text-foreground">{user.username || 'User'}</h2>
                  {user.is_expert && (
                    <span className="text-xs font-bold px-4 py-1.5 rounded-full bg-gradient-to-r from-warning/20 to-warning/20 text-warning dark:text-warning border border-warning/30 shadow-sm">
                      ✦ Expert
                    </span>
                  )}
                  <span className="text-xs font-semibold px-4 py-1.5 rounded-full bg-success/10 text-success border border-success/20">
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
                  <span className="flex items-center gap-2 px-4 py-2 rounded-full bg-success/10">
                    <div className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-success"></span>
                    </div>
                    <span className="text-success">Active now</span>
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
          gradient="from-info to-primary"
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
                  <div className="w-2 h-2 rounded-full bg-warning animate-pulse" />
                  <span className="text-warning font-medium">Unsaved changes</span>
                </>
              ) : (
                <>
                  <div className="w-2 h-2 rounded-full bg-success" />
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
          gradient="from-success to-success"
        />
        <StatsCard
          title="Last Login"
          value="Current Session"
          subtitle="Security stats coming soon"
          icon={Clock}
          gradient="from-info to-primary"
        />
        <StatsCard
          title="Active Sessions"
          value="—"
          subtitle="Session tracking coming soon"
          icon={Monitor}
          gradient="from-primary to-brand-2"
        />
      </div>

      {/* Authentication Settings */}
      <SectionCard
        title="Authentication"
        description="Manage your password and security settings"
        icon={Shield}
        gradient="from-success to-success"
      >
        <div className="space-y-1">
          <SettingRow
            icon={Lock}
            title="Password"
            description="Use a strong password that you don't use elsewhere"
            iconColor="text-info"
            iconBg="bg-info/10"
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
            iconColor="text-warning"
            iconBg="bg-warning/10"
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
        gradient="from-primary to-brand-2"
      >
        <div className="rounded-xl border border-success/20 bg-success/5 p-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-xl bg-success/10">
                <Monitor className="h-5 w-5 text-success" />
              </div>
              <div>
                <p className="font-medium text-foreground flex items-center gap-2">
                  Current Device
                  <span className="text-xs font-semibold text-success bg-success/10 px-2 py-0.5 rounded-full">
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
        className="border-destructive/20"
        gradient="from-destructive to-destructive"
      >
        <SettingRow
          icon={Trash2}
          title="Delete Account"
          description="Permanently delete your account and all associated data. This action cannot be undone."
          iconColor="text-destructive"
          iconBg="bg-destructive/10"
        >
          <Button
            variant="outline"
            className="text-destructive hover:text-destructive border-destructive/30 hover:border-destructive/50 hover:bg-destructive/5 rounded-xl"
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

  const renderModelsSection = () => <RuntimeInfoPanel />

  const renderContent = () => {
    switch (activeTab) {
      case 'profile':
        return renderProfileSection()
      case 'security':
        return renderSecuritySection()
      case 'llm-providers':
        return <LLMProviderSettings />
      case 'embeddings':
        return <EmbeddingSettings onOpenProviders={() => setActiveTab('llm-providers')} />
      case 'catalogue':
        return <ModelCatalogPanel />
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
        <PageHeader
          icon={<Settings2 />}
          title="Settings"
          description="Your account, security, LLM providers and how this deployment routes requests."
          className="mb-10"
        />

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
                  <div className="p-3 rounded-xl bg-info/10">
                    <Info className="h-5 w-5 text-info" />
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
              <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center gap-3">
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
    </div>
  )
}
