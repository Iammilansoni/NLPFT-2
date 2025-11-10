'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { GlowButton } from '@/components/ui/glow-button'
import { 
  Terminal, 
  Sparkles, 
  Zap, 
  CheckCircle2, 
  Code2, 
  Database,
  ArrowRight,
  Play,
  Cpu,
  FileCode,
  GitBranch
} from 'lucide-react'

const demoSteps = [
  {
    id: 'input',
    title: 'Natural Language Input',
    icon: Terminal,
    color: 'from-blue-500 to-cyan-500',
    content: {
      type: 'terminal',
      text: 'Create tests for user authentication with email and password',
    }
  },
  {
    id: 'analysis',
    title: 'AI Analysis',
    icon: Sparkles,
    color: 'from-purple-500 to-pink-500',
    content: {
      type: 'analysis',
      items: [
        { label: 'Intent Detected', value: 'Authentication', confidence: 98 },
        { label: 'Entities Found', value: 'email, password', confidence: 95 },
        { label: 'Test Type', value: 'Integration', confidence: 92 },
      ]
    }
  },
  {
    id: 'generation',
    title: 'Test Generation',
    icon: Code2,
    color: 'from-green-500 to-emerald-500',
    content: {
      type: 'code',
      code: `describe('User Authentication', () => {
  test('valid credentials', async () => {
    const response = await api.post('/auth/login', {
      email: 'user@example.com',
      password: 'SecurePass123!'
    });
    expect(response.status).toBe(200);
    expect(response.data.token).toBeDefined();
  });
  
  test('invalid email format', async () => {
    const response = await api.post('/auth/login', {
      email: 'invalid-email',
      password: 'SecurePass123!'
    });
    expect(response.status).toBe(400);
  });
});`
    }
  },
  {
    id: 'results',
    title: 'Instant Results',
    icon: CheckCircle2,
    color: 'from-orange-500 to-red-500',
    content: {
      type: 'results',
      stats: [
        { label: 'Tests Generated', value: '127', icon: FileCode },
        { label: 'Coverage', value: '98.5%', icon: GitBranch },
        { label: 'Execution Time', value: '2.3s', icon: Zap },
        { label: 'Success Rate', value: '100%', icon: CheckCircle2 },
      ]
    }
  }
]

export function InteractiveShowcase() {
  const [activeStep, setActiveStep] = useState(0)

  return (
    <section className="relative py-20 md:py-32 overflow-hidden border-t">
      {/* Background */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute inset-0 bg-gradient-to-b from-background via-primary/5 to-background" />
        <motion.div
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.1, 0.2, 0.1],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: "easeInOut"
          }}
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-accent/20 rounded-full blur-3xl"
        />
      </div>

      <div className="container mx-auto px-4">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-center mb-16 space-y-4"
        >
          <Badge variant="outline" className="px-4 py-1.5">
            <Cpu className="mr-2 h-3.5 w-3.5" />
            See It In Action
          </Badge>
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold font-heading">
            From Idea to{' '}
            <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              Production Tests
            </span>
            {' '}in Seconds
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Watch how NLPForge transforms your plain English into comprehensive test suites
          </p>
        </motion.div>

        <div className="max-w-6xl mx-auto">
          {/* Step Navigation */}
          <div className="flex justify-center mb-12 overflow-x-auto pb-4">
            <div className="flex gap-2 md:gap-4">
              {demoSteps.map((step, index) => {
                const StepIcon = step.icon
                const isActive = activeStep === index
                const isCompleted = activeStep > index
                
                return (
                  <motion.button
                    key={step.id}
                    onClick={() => setActiveStep(index)}
                    className={`flex items-center gap-3 px-4 md:px-6 py-3 rounded-xl border-2 transition-all ${
                      isActive 
                        ? 'border-primary bg-primary/10 shadow-glow' 
                        : isCompleted
                        ? 'border-success/50 bg-success/5'
                        : 'border-border hover:border-primary/50'
                    }`}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <div className={`h-10 w-10 rounded-lg flex items-center justify-center ${
                      isActive 
                        ? `bg-gradient-to-br ${step.color} text-white shadow-lg` 
                        : isCompleted
                        ? 'bg-success/20 text-success'
                        : 'bg-muted text-muted-foreground'
                    }`}>
                      {isCompleted ? (
                        <CheckCircle2 className="h-5 w-5" />
                      ) : (
                        <StepIcon className="h-5 w-5" />
                      )}
                    </div>
                    <div className="hidden md:block text-left">
                      <div className="text-xs text-muted-foreground">Step {index + 1}</div>
                      <div className="text-sm font-semibold">{step.title}</div>
                    </div>
                  </motion.button>
                )
              })}
            </div>
          </div>

          {/* Content Display */}
          <AnimatePresence mode="wait">
            <motion.div
              key={activeStep}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <Card className="border-2 overflow-hidden glass-card shadow-glow-lg">
                <CardContent className="p-8 md:p-12">
                  {demoSteps[activeStep].content.type === 'terminal' && (
                    <div className="space-y-4">
                      <div className="flex items-center gap-3 mb-6">
                        <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center text-white shadow-lg">
                          <Terminal className="h-6 w-6" />
                        </div>
                        <div>
                          <h3 className="text-xl font-bold">Natural Language Input</h3>
                          <p className="text-sm text-muted-foreground">Just describe what you want to test</p>
                        </div>
                      </div>
                      <div className="p-6 rounded-xl bg-black/90 border-2 border-primary/30 font-mono">
                        <div className="flex items-center gap-2 mb-4 pb-3 border-b border-primary/20">
                          <div className="flex gap-1.5">
                            <div className="w-3 h-3 rounded-full bg-red-500" />
                            <div className="w-3 h-3 rounded-full bg-yellow-500" />
                            <div className="w-3 h-3 rounded-full bg-green-500" />
                          </div>
                          <span className="text-xs text-muted-foreground ml-2">nlpforge-cli</span>
                        </div>
                        <div className="space-y-2">
                          <div className="flex items-center gap-2 text-primary">
                            <span>$</span>
                            <motion.span
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              transition={{ duration: 0.5 }}
                            >
                              {demoSteps[activeStep].content.text}
                            </motion.span>
                          </div>
                          <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.5 }}
                            className="text-emerald-400 flex items-center gap-2"
                          >
                            <Zap className="h-4 w-4" />
                            <span>Processing...</span>
                          </motion.div>
                        </div>
                      </div>
                    </div>
                  )}

                  {demoSteps[activeStep].content.type === 'analysis' && (
                    <div className="space-y-6">
                      <div className="flex items-center gap-3 mb-6">
                        <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white shadow-lg">
                          <Sparkles className="h-6 w-6" />
                        </div>
                        <div>
                          <h3 className="text-xl font-bold">AI Analysis</h3>
                          <p className="text-sm text-muted-foreground">Understanding your requirements</p>
                        </div>
                      </div>
                      {demoSteps[activeStep].content.items?.map((item, i) => (
                        <motion.div
                          key={item.label}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: i * 0.1 }}
                          className="p-4 rounded-xl bg-card/50 border"
                        >
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-semibold">{item.label}</span>
                            <Badge className="bg-primary/10 text-primary border-primary/30">
                              {item.confidence}% confidence
                            </Badge>
                          </div>
                          <div className="text-lg font-bold text-primary">{item.value}</div>
                          <div className="mt-2 h-2 bg-muted rounded-full overflow-hidden">
                            <motion.div
                              initial={{ width: 0 }}
                              animate={{ width: `${item.confidence}%` }}
                              transition={{ duration: 1, delay: i * 0.1 + 0.3 }}
                              className="h-full bg-gradient-to-r from-primary to-accent"
                            />
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  )}

                  {demoSteps[activeStep].content.type === 'code' && (
                    <div className="space-y-4">
                      <div className="flex items-center gap-3 mb-6">
                        <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-green-500 to-emerald-500 flex items-center justify-center text-white shadow-lg">
                          <Code2 className="h-6 w-6" />
                        </div>
                        <div>
                          <h3 className="text-xl font-bold">Generated Test Suite</h3>
                          <p className="text-sm text-muted-foreground">Production-ready code</p>
                        </div>
                      </div>
                      <div className="p-6 rounded-xl bg-black/90 border-2 border-success/30 font-mono text-sm overflow-x-auto">
                        <div className="flex items-center gap-2 mb-4 pb-3 border-b border-success/20">
                          <div className="flex gap-1.5">
                            <div className="w-3 h-3 rounded-full bg-red-500" />
                            <div className="w-3 h-3 rounded-full bg-yellow-500" />
                            <div className="w-3 h-3 rounded-full bg-green-500" />
                          </div>
                          <span className="text-xs text-muted-foreground ml-2">auth.test.ts</span>
                        </div>
                        <pre className="text-emerald-400">
                          <code>{demoSteps[activeStep].content.code}</code>
                        </pre>
                      </div>
                    </div>
                  )}

                  {demoSteps[activeStep].content.type === 'results' && (
                    <div className="space-y-6">
                      <div className="flex items-center gap-3 mb-6">
                        <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center text-white shadow-lg">
                          <CheckCircle2 className="h-6 w-6" />
                        </div>
                        <div>
                          <h3 className="text-xl font-bold">Instant Results</h3>
                          <p className="text-sm text-muted-foreground">Comprehensive test coverage achieved</p>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {demoSteps[activeStep].content.stats?.map((stat, i) => {
                          const StatIcon = stat.icon
                          return (
                            <motion.div
                              key={stat.label}
                              initial={{ opacity: 0, scale: 0.8 }}
                              animate={{ opacity: 1, scale: 1 }}
                              transition={{ delay: i * 0.1 }}
                              className="p-4 rounded-xl bg-gradient-to-br from-success/10 to-emerald-500/5 border-2 border-success/30 text-center"
                            >
                              <StatIcon className="h-8 w-8 text-success mx-auto mb-2" />
                              <div className="text-2xl font-bold text-success">{stat.value}</div>
                              <div className="text-xs text-muted-foreground mt-1">{stat.label}</div>
                            </motion.div>
                          )
                        })}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          </AnimatePresence>

          {/* Navigation Buttons */}
          <div className="flex justify-center gap-4 mt-8">
            <GlowButton
              variant="outline"
              onClick={() => setActiveStep(Math.max(0, activeStep - 1))}
              disabled={activeStep === 0}
              className="disabled:opacity-50"
            >
              Previous
            </GlowButton>
            {activeStep < demoSteps.length - 1 ? (
              <GlowButton
                onClick={() => setActiveStep(Math.min(demoSteps.length - 1, activeStep + 1))}
              >
                Next Step
                <ArrowRight className="ml-2 h-4 w-4" />
              </GlowButton>
            ) : (
              <GlowButton>
                <Play className="mr-2 h-4 w-4" />
                Try It Now
              </GlowButton>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}
