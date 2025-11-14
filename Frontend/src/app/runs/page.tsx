'use client'

import { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import Link from 'next/link'
import {
  Filter,
  Calendar,
  CheckCircle2,
  XCircle,
  Clock,
  Play,
  AlertCircle,
  TrendingUp,
  Search as SearchIcon,
  FileCode,
  Activity,
  ChevronRight,
  Loader2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'
import { formatDistanceToNow } from 'date-fns'

interface Run {
  id: string
  query: string
  intent: string
  status: 'passed' | 'failed' | 'running' | 'pending'
  confidence: number
  matches: number
  duration: number
  timestamp: string
  template?: string
  tests: number
}

// Store runs in memory (in a real app, this would come from a backend)
let runHistory: Run[] = []
let runIdCounter = 1

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] } },
}

export default function RunsPage() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | Run['status']>('all')
  const [runs, setRuns] = useState<Run[]>(runHistory)

  const filteredRuns = useMemo(() => {
    return runs.filter((run) => {
      const matchesSearch =
        run.query.toLowerCase().includes(search.toLowerCase()) ||
        run.intent.toLowerCase().includes(search.toLowerCase())
      const matchesStatus = statusFilter === 'all' || run.status === statusFilter
      return matchesSearch && matchesStatus
    })
  }, [runs, search, statusFilter])

  const statusCounts = useMemo(() => ({
    all: runs.length,
    passed: runs.filter((r) => r.status === 'passed').length,
    failed: runs.filter((r) => r.status === 'failed').length,
    running: runs.filter((r) => r.status === 'running').length,
    pending: runs.filter((r) => r.status === 'pending').length,
  }), [runs])

  const isLoading = false

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      <div className="p-6 lg:p-8 space-y-8 max-w-[1600px] mx-auto">
        {/* Header */}
        <motion.div initial="hidden" animate="show" variants={fadeUp}>
          <div className="flex items-start justify-between mb-6">
            <div className="flex items-center gap-4">
              <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-violet-500 via-purple-500 to-violet-600 flex items-center justify-center text-white shadow-lg shadow-violet-500/25">
                <Activity className="h-7 w-7" />
              </div>
              <div>
                <h1 className="text-4xl font-bold tracking-tight">Test Runs</h1>
                <p className="text-muted-foreground mt-1">
                  View and manage your test execution history
                </p>
              </div>
            </div>
            <Link href="/run/new">
              <Button size="lg" className="gap-2 shadow-lg">
                <Play className="h-5 w-5" />
                New Run
              </Button>
            </Link>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <StatCard
              label="All Runs"
              value={statusCounts.all}
              active={statusFilter === 'all'}
              onClick={() => setStatusFilter('all')}
              gradient="from-blue-500 to-cyan-500"
            />
            <StatCard
              label="Passed"
              value={statusCounts.passed}
              active={statusFilter === 'passed'}
              onClick={() => setStatusFilter('passed')}
              gradient="from-emerald-500 to-green-500"
              icon={<CheckCircle2 className="h-4 w-4" />}
            />
            <StatCard
              label="Failed"
              value={statusCounts.failed}
              active={statusFilter === 'failed'}
              onClick={() => setStatusFilter('failed')}
              gradient="from-red-500 to-rose-500"
              icon={<XCircle className="h-4 w-4" />}
            />
            <StatCard
              label="Running"
              value={statusCounts.running}
              active={statusFilter === 'running'}
              onClick={() => setStatusFilter('running')}
              gradient="from-orange-500 to-amber-500"
              icon={<Loader2 className="h-4 w-4 animate-spin" />}
            />
            <StatCard
              label="Pending"
              value={statusCounts.pending}
              active={statusFilter === 'pending'}
              onClick={() => setStatusFilter('pending')}
              gradient="from-gray-500 to-slate-500"
              icon={<Clock className="h-4 w-4" />}
            />
          </div>
        </motion.div>

        {/* Search */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <div className="relative max-w-xl">
            <SearchIcon className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <Input
              placeholder="Search runs by query or intent..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-12 h-12 border-2"
            />
          </div>
        </motion.div>

        {/* Runs List */}
        {isLoading ? (
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <Card key={i} className="border-2">
                <CardContent className="p-6">
                  <Skeleton className="h-6 w-3/4 mb-3" />
                  <Skeleton className="h-4 w-1/2" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : runs.length === 0 ? (
          <Card className="border-2">
            <CardContent className="py-16 text-center">
              <div className="h-16 w-16 rounded-2xl bg-muted flex items-center justify-center mx-auto mb-4">
                <AlertCircle className="h-8 w-8 text-muted-foreground" />
              </div>
              <h3 className="text-xl font-semibold mb-2">No runs found</h3>
              <p className="text-muted-foreground mb-6">
                {search || statusFilter !== 'all'
                  ? 'Try adjusting your filters'
                  : 'Start by creating your first test run'}
              </p>
              <Link href="/run/new">
                <Button size="lg" className="gap-2">
                  <Play className="h-5 w-5" />
                  Create New Run
                </Button>
              </Link>
            </CardContent>
          </Card>
          ) : (
          <div className="space-y-4">
            {filteredRuns.map((run, index) => (
              <RunCard key={run.id} run={run} index={index} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}function StatCard({
  label,
  value,
  active,
  onClick,
  gradient,
  icon,
}: {
  label: string
  value: number
  active: boolean
  onClick: () => void
  gradient: string
  icon?: React.ReactNode
}) {
  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={cn(
        'relative overflow-hidden rounded-xl p-4 text-left transition-all border-2',
        active
          ? 'border-primary bg-primary/5 shadow-lg'
          : 'border-transparent bg-card hover:border-primary/30 hover:shadow-md'
      )}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-muted-foreground">{label}</span>
        {icon && <div className="text-muted-foreground">{icon}</div>}
      </div>
      <div className="text-2xl font-bold">{value}</div>
      {active && (
        <motion.div
          layoutId="active-filter"
          className={cn('absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r', gradient)}
          transition={{ type: 'spring', stiffness: 380, damping: 30 }}
        />
      )}
    </motion.button>
  )
}

function RunCard({ run, index }: { run: Run; index: number }) {
  const statusConfig = {
    passed: {
      gradient: 'from-emerald-500 to-green-500',
      icon: CheckCircle2,
      bg: 'bg-emerald-50 dark:bg-emerald-950/20',
      border: 'border-emerald-200 dark:border-emerald-800',
    },
    failed: {
      gradient: 'from-red-500 to-rose-500',
      icon: XCircle,
      bg: 'bg-red-50 dark:bg-red-950/20',
      border: 'border-red-200 dark:border-red-800',
    },
    running: {
      gradient: 'from-orange-500 to-amber-500',
      icon: Loader2,
      bg: 'bg-orange-50 dark:bg-orange-950/20',
      border: 'border-orange-200 dark:border-orange-800',
    },
    pending: {
      gradient: 'from-gray-500 to-slate-500',
      icon: Clock,
      bg: 'bg-gray-50 dark:bg-gray-950/20',
      border: 'border-gray-200 dark:border-gray-800',
    },
  }

  const config = statusConfig[run.status]
  const Icon = config.icon

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
    >
      <Link href={`/runs/${run.id}`}>
        <Card className="border-2 hover:border-primary/30 hover:shadow-lg transition-all group cursor-pointer">
          <CardContent className="p-6">
            <div className="flex items-start gap-4">
              {/* Status Icon */}
              <div
                className={cn(
                  'flex-shrink-0 h-14 w-14 rounded-xl flex items-center justify-center text-white shadow-md bg-gradient-to-br',
                  config.gradient
                )}
              >
                <Icon className={cn('h-7 w-7', run.status === 'running' && 'animate-spin')} />
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-lg group-hover:text-primary transition-colors mb-2 truncate">
                  {run.query}
                </h3>

                <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground mb-3">
                  <Badge variant="outline" className="capitalize">
                    {run.intent}
                  </Badge>
                  {run.template && (
                    <div className="flex items-center gap-1">
                      <FileCode className="h-3 w-3" />
                      <code className="text-xs">{run.template}</code>
                    </div>
                  )}
                  <div className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    <span className="text-xs">
                      {formatDistanceToNow(new Date(run.timestamp), { addSuffix: true })}
                    </span>
                  </div>
                </div>

                {/* Metrics */}
                <div className="flex flex-wrap items-center gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
                      <TrendingUp className="h-4 w-4 text-primary" />
                    </div>
                    <div>
                      <div className="font-semibold">{Math.round(run.confidence * 100)}%</div>
                      <div className="text-xs text-muted-foreground">Confidence</div>
                    </div>
                  </div>

                  {run.status !== 'running' && run.status !== 'pending' && (
                    <>
                      <div className="h-10 w-px bg-border" />
                      <div>
                        <div className="font-semibold">{run.tests}</div>
                        <div className="text-xs text-muted-foreground">Tests</div>
                      </div>
                      <div className="h-10 w-px bg-border" />
                      <div>
                        <div className="font-semibold">{run.matches}</div>
                        <div className="text-xs text-muted-foreground">Matches</div>
                      </div>
                      <div className="h-10 w-px bg-border" />
                      <div>
                        <div className="font-semibold">{run.duration}ms</div>
                        <div className="text-xs text-muted-foreground">Duration</div>
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* Arrow */}
              <ChevronRight className="flex-shrink-0 h-6 w-6 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all" />
            </div>
          </CardContent>
        </Card>
      </Link>
    </motion.div>
  )
}
