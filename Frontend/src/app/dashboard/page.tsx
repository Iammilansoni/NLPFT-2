'use client'

import { useMemo, useState } from 'react'
import dynamic from 'next/dynamic'
import { motion, AnimatePresence } from 'framer-motion'
import Link from 'next/link'
import {
  BarChart3,
  CheckCircle2,
  Clock,
  FileCode,
  Plus,
  TrendingUp,
  Activity,
  AlertCircle,
  Brain,
  Sparkles,
  Zap,
  ArrowRight,
  Play,
  Database,
  X,
  LayoutDashboard,
  Target,
  Timer,
  Layers,
  ChevronRight,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { useRouter } from 'next/navigation'
import { useQueryStats } from '@/hooks/useQuery'
import { useTemplateStats } from '@/hooks/useTemplates'

const TrendChart = dynamic(
  () => import('@/components/dashboard/trend-chart').then((m) => m.TrendChart),
  {
    ssr: false,
    loading: () => (
      <div className="h-64">
        <div className="animate-pulse h-full w-full rounded-xl bg-muted" />
      </div>
    ),
  }
)

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] } },
}

export default function DashboardPage() {
  const router = useRouter()
  const [query, setQuery] = useState('')

  // Use our custom hooks for backend data
  const { data: stats, isLoading, error } = useQueryStats()
  const { data: templateStats, isLoading: templatesLoading, error: templatesError } = useTemplateStats()

  // Calculate detailed health status
  const backendHealthy = !error && !!stats
  const databaseHealthy = !!stats && typeof stats.total_embeddings === 'number' && stats.total_embeddings >= 0
  const templatesHealthy = !templatesError && !!templateStats

  const allHealthy = backendHealthy && databaseHealthy && templatesHealthy
  const anyIssues = !!error || !!templatesError || !stats
  const isLoading_ = isLoading || templatesLoading

  const recentRuns = [
    {
      id: '1',
      query: 'Login with email and password',
      status: 'passed',
      time: '2m ago',
      tests: 12,
      confidence: 95,
    },
    {
      id: '2',
      query: 'Create new user account',
      status: 'failed',
      time: '15m ago',
      tests: 8,
      confidence: 87,
    },
    {
      id: '3',
      query: 'Update user profile',
      status: 'passed',
      time: '1h ago',
      tests: 15,
      confidence: 92,
    },
    {
      id: '4',
      query: 'Delete user by ID',
      status: 'passed',
      time: '2h ago',
      tests: 6,
      confidence: 89,
    },
  ]

  const quickActions = [
    { label: 'Login test', icon: '🔐', query: 'Test login with credentials' },
    { label: 'Create user', icon: '👤', query: 'Create new user account' },
    { label: 'Update profile', icon: '✏️', query: 'Update user profile' },
    { label: 'Delete user', icon: '🗑️', query: 'Delete user by ID' },
  ]

  function handleQuickRun(e: React.FormEvent) {
    e.preventDefault()
    if (!query.trim()) return
    router.push(`/run/new?query=${encodeURIComponent(query.trim())}`)
  }

  const topIntents = useMemo(() => {
    if (!stats?.intents) return []
    return Object.entries(stats.intents)
      .sort((a, b) => (b[1] as number) - (a[1] as number))
      .slice(0, 5)
  }, [stats])

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      <div className="p-6 lg:p-8 space-y-8 max-w-[1600px] mx-auto">
        {/* Header */}
        <motion.div
          initial="hidden"
          animate="show"
          variants={fadeUp}
          className="flex flex-col gap-6"
        >
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-primary via-primary to-accent flex items-center justify-center text-white shadow-lg shadow-primary/25">
                <LayoutDashboard className="h-7 w-7" />
              </div>
              <div>
                <h1 className="text-4xl font-bold tracking-tight">Dashboard</h1>
                <p className="text-muted-foreground mt-1">
                  Monitor and manage your AI-powered test automation
                </p>
              </div>
            </div>
            
            {/* Health Indicator */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2 }}
              className="flex flex-col items-end gap-2"
            >
              {isLoading_ ? (
                <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-muted/50">
                  <div className="h-2 w-2 rounded-full bg-gray-400 animate-pulse" />
                  <span className="text-sm font-medium text-muted-foreground">Connecting...</span>
                </div>
              ) : allHealthy ? (
                <>
                  <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                    <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="text-sm font-medium text-emerald-700 dark:text-emerald-400">All Systems Operational</span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <div className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                      <span>Backend API</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <div className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                      <span>Database ({stats?.index_name || 'Redis'})</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <div className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                      <span>Templates</span>
                    </div>
                  </div>
                </>
              ) : anyIssues ? (
                <>
                  <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-red-500/10 border border-red-500/20">
                    <div className="h-2 w-2 rounded-full bg-red-500" />
                    <span className="text-sm font-medium text-red-700 dark:text-red-400">System Issues Detected</span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <div className={cn(
                        "h-1.5 w-1.5 rounded-full",
                        backendHealthy ? "bg-emerald-500" : "bg-red-500"
                      )} />
                      <span>Backend API</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <div className={cn(
                        "h-1.5 w-1.5 rounded-full",
                        databaseHealthy ? "bg-emerald-500" : "bg-red-500"
                      )} />
                      <span>Database</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <div className={cn(
                        "h-1.5 w-1.5 rounded-full",
                        templatesHealthy ? "bg-emerald-500" : "bg-red-500"
                      )} />
                      <span>Templates</span>
                    </div>
                  </div>
                </>
              ) : (
                <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-amber-500/10 border border-amber-500/20">
                  <div className="h-2 w-2 rounded-full bg-amber-500" />
                  <span className="text-sm font-medium text-amber-700 dark:text-amber-400">Degraded Performance</span>
                </div>
              )}
            </motion.div>
          </div>

          {/* Quick Run Card */}
          <Card className="border-2 border-primary/20 bg-gradient-to-br from-primary/5 via-background to-accent/5 shadow-lg">
            <CardContent className="p-6">
              <form onSubmit={handleQuickRun} className="space-y-4">
                <div className="flex items-center gap-3 mb-4">
                  <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center text-white shadow-md">
                    <Sparkles className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg">Quick Test Run</h3>
                    <p className="text-sm text-muted-foreground">
                      Describe your test in plain English
                    </p>
                  </div>
                </div>

                <div className="relative">
                  <Input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="e.g., Test login with email user@example.com and password P@ssw0rd"
                    className="h-14 pr-32 text-base border-2 focus:border-primary"
                  />
                  <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-2">
                    {query && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => setQuery('')}
                        className="h-8 w-8 p-0"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    )}
                    <Button type="submit" size="sm" className="h-10 gap-2" disabled={!query.trim()}>
                      <Play className="h-4 w-4" />
                      Run
                    </Button>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  {quickActions.map((action) => (
                    <button
                      key={action.label}
                      type="button"
                      onClick={() => setQuery(action.query)}
                      className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-muted/60 hover:bg-muted transition-colors text-sm"
                    >
                      <span>{action.icon}</span>
                      <span>{action.label}</span>
                    </button>
                  ))}
                </div>
              </form>
            </CardContent>
          </Card>
        </motion.div>

        {/* Stats Grid */}
        <motion.div
          initial="hidden"
          animate="show"
          variants={{
            show: { transition: { staggerChildren: 0.1 } },
          }}
          className="grid gap-6 md:grid-cols-2 lg:grid-cols-4"
        >
          <StatCard
            title="Total Vectors"
            value={stats?.total_embeddings?.toLocaleString() ?? '0'}
            change="+12%"
            trend="up"
            icon={<Database className="h-5 w-5" />}
            gradient="from-blue-500 to-cyan-500"
          />
          <StatCard
            title="Test Runs"
            value="0"
            change="+8%"
            trend="up"
            icon={<Activity className="h-5 w-5" />}
            gradient="from-violet-500 to-purple-500"
          />
          <StatCard
            title="Templates"
            value={templateStats?.total_templates ?? 0}
            change="2 new"
            trend="neutral"
            icon={<FileCode className="h-5 w-5" />}
            gradient="from-emerald-500 to-green-500"
          />
          <StatCard
            title="Intents"
            value={Object.keys(stats?.intents ?? {}).length ?? 0}
            change="+5"
            trend="up"
            icon={<Layers className="h-5 w-5" />}
            gradient="from-orange-500 to-amber-500"
          />
        </motion.div>

        {/* Main Content Grid */}
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Recent Activity */}
          <div className="lg:col-span-2 space-y-6">
            <Card className="border-2">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center text-white shadow-md">
                      <Activity className="h-5 w-5" />
                    </div>
                    <div>
                      <CardTitle>Recent Activity</CardTitle>
                      <CardDescription>Latest test runs and results</CardDescription>
                    </div>
                  </div>
                  <Link href="/runs">
                    <Button variant="ghost" size="sm" className="gap-2">
                      View all
                      <ArrowRight className="h-4 w-4" />
                    </Button>
                  </Link>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {recentRuns.map((run) => (
                  <Link key={run.id} href={`/runs/${run.id}`}>
                    <motion.div
                      whileHover={{ x: 4 }}
                      className="group flex items-center gap-4 p-4 rounded-xl border-2 border-transparent hover:border-primary/20 hover:bg-muted/50 transition-all cursor-pointer"
                    >
                      <div
                        className={cn(
                          'h-12 w-12 rounded-xl flex items-center justify-center text-white shadow-md',
                          run.status === 'passed'
                            ? 'bg-gradient-to-br from-emerald-500 to-green-500'
                            : 'bg-gradient-to-br from-red-500 to-rose-500'
                        )}
                      >
                        {run.status === 'passed' ? (
                          <CheckCircle2 className="h-6 w-6" />
                        ) : (
                          <AlertCircle className="h-6 w-6" />
                        )}
                      </div>

                      <div className="flex-1 min-w-0">
                        <p className="font-semibold group-hover:text-primary transition-colors truncate">
                          {run.query}
                        </p>
                        <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            <span>{run.time}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <FileCode className="h-3 w-3" />
                            <span>{run.tests} tests</span>
                          </div>
                          <Badge variant="secondary" className="text-xs">
                            {run.confidence}% confidence
                          </Badge>
                        </div>
                      </div>

                      <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
                    </motion.div>
                  </Link>
                ))}
              </CardContent>
            </Card>

            {/* Performance Chart */}
            <Card className="border-2">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-500 flex items-center justify-center text-white shadow-md">
                    <TrendingUp className="h-5 w-5" />
                  </div>
                  <div>
                    <CardTitle>Performance Trends</CardTitle>
                    <CardDescription>Test execution metrics over time</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <TrendChart />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Top Intents */}
            <Card className="border-2">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-emerald-500 to-green-500 flex items-center justify-center text-white shadow-md">
                    <Target className="h-5 w-5" />
                  </div>
                  <div>
                    <CardTitle>Top Intents</CardTitle>
                    <CardDescription>Most used test intents</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {isLoading ? (
                  <>
                    {[...Array(5)].map((_, i) => (
                      <Skeleton key={i} className="h-12 w-full" />
                    ))}
                  </>
                ) : topIntents.length > 0 ? (
                  topIntents.map(([intent, count], idx) => {
                    const max = topIntents[0][1] as number
                    const percent = Math.round(((count as number) / max) * 100)
                    return (
                      <div key={intent} className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="font-medium capitalize">{intent}</span>
                          <span className="text-muted-foreground">{count}</span>
                        </div>
                        <div className="h-2 bg-muted rounded-full overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${percent}%` }}
                            transition={{ duration: 0.7, delay: idx * 0.1 }}
                            className="h-full bg-gradient-to-r from-primary to-accent rounded-full"
                          />
                        </div>
                      </div>
                    )
                  })
                ) : (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No intents data available
                  </p>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}

function StatCard({
  title,
  value,
  change,
  trend,
  icon,
  gradient,
}: {
  title: string
  value: string | number
  change?: string
  trend?: 'up' | 'down' | 'neutral'
  icon: React.ReactNode
  gradient: string
}) {
  return (
    <motion.div variants={fadeUp}>
      <Card className="border-2 hover:border-primary/30 transition-all hover:shadow-lg group">
        <CardContent className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="text-sm font-medium text-muted-foreground">{title}</div>
            <div
              className={cn(
                'h-10 w-10 rounded-xl bg-gradient-to-br flex items-center justify-center text-white shadow-md group-hover:scale-110 transition-transform',
                gradient
              )}
            >
              {icon}
            </div>
          </div>
          <div className="text-3xl font-bold tracking-tight mb-2">{value}</div>
          {change && (
            <div className="flex items-center gap-2 text-sm">
              {trend === 'up' && <TrendingUp className="h-4 w-4 text-emerald-600" />}
              {trend === 'down' && <TrendingUp className="h-4 w-4 text-red-600 rotate-180" />}
              <span
                className={cn(
                  'font-medium',
                  trend === 'up'
                    ? 'text-emerald-600'
                    : trend === 'down'
                    ? 'text-red-600'
                    : 'text-muted-foreground'
                )}
              >
                {change}
              </span>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )
}
