'use client'

import { motion, useInView, useMotionValue, useSpring } from 'framer-motion'
import { useEffect, useRef } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Quote } from 'lucide-react'

const stats = [
  { value: 50000, suffix: '+', label: 'Tests Run Daily', duration: 2 },
  { value: 45, suffix: 'ms', label: 'Avg Latency', duration: 1.5 },
  { value: 94.2, suffix: '%', label: 'Pass Rate', duration: 2 },
  { value: 99.9, suffix: '%', label: 'Uptime SLA', duration: 2 },
]

const testimonials = [
  {
    quote: 'NLPForge cut our test creation time by 70%. The AI understands context better than our manual scripts ever did.',
    author: 'Sarah Chen',
    role: 'QA Lead',
    company: 'FinTech Corp',
    avatar: 'SC',
  },
  {
    quote: 'The confidence scoring gives us transparency we never had before. We trust the AI because we understand its decisions.',
    author: 'Marcus Rodriguez',
    role: 'Engineering Manager',
    company: 'HealthTech Solutions',
    avatar: 'MR',
  },
  {
    quote: 'Incremental enrichment means our test suite gets smarter every day. It learns from production without manual intervention.',
    author: 'Aisha Patel',
    role: 'DevOps Architect',
    company: 'Global Payments Inc',
    avatar: 'AP',
  },
]

function AnimatedCounter({ value, suffix, duration }: { value: number; suffix: string; duration: number }) {
  const ref = useRef<HTMLSpanElement>(null)
  const motionValue = useMotionValue(0)
  const springValue = useSpring(motionValue, { duration: duration * 1000 })
  const isInView = useInView(ref, { once: true, margin: '-100px' })

  useEffect(() => {
    if (isInView) {
      motionValue.set(value)
    }
  }, [isInView, motionValue, value])

  useEffect(() => {
    springValue.on('change', (latest) => {
      if (ref.current) {
        ref.current.textContent = latest.toFixed(suffix === '%' ? 1 : 0)
      }
    })
  }, [springValue, suffix])

  return (
    <span ref={ref} className="tabular-nums">
      0
    </span>
  )
}

export function MetricsProof() {
  return (
    <section className="py-12 md:py-16 bg-muted/30 border-t">
      <div className="container mx-auto px-4">
        {/* Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="mb-20"
        >
          <div className="text-center mb-12 space-y-4">
            <Badge variant="outline" className="px-4 py-1.5">
              Trusted by Teams
            </Badge>
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold font-heading">
              Numbers That{' '}
              <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                Speak for Themselves
              </span>
            </h2>
          </div>

          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
            {stats.map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: index * 0.1 }}
              >
                <Card className="border-2 text-center">
                  <CardContent className="p-8 space-y-2">
                    <div className="text-4xl md:text-5xl font-bold font-heading bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                      <AnimatedCounter value={stat.value} suffix={stat.suffix} duration={stat.duration} />
                      {stat.suffix}
                    </div>
                    <p className="text-sm text-muted-foreground font-medium">{stat.label}</p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Testimonials */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          <div className="text-center mb-12">
            <h3 className="text-2xl md:text-3xl font-bold font-heading">
              What Teams Are Saying
            </h3>
          </div>

          <div className="grid gap-8 md:grid-cols-3">
            {testimonials.map((testimonial, index) => (
              <motion.div
                key={testimonial.author}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
              >
                <Card className="h-full border-2 hover:border-primary/50 transition-all duration-300 hover:shadow-lg">
                  <CardContent className="p-6 space-y-4">
                    <Quote className="h-8 w-8 text-primary/20" />
                    <p className="text-muted-foreground leading-relaxed">
                      &quot;{testimonial.quote}&quot;
                    </p>
                    <div className="flex items-center gap-3 pt-4 border-t">
                      <div className="h-12 w-12 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center text-white font-bold text-sm">
                        {testimonial.avatar}
                      </div>
                      <div>
                        <div className="font-semibold">{testimonial.author}</div>
                        <div className="text-sm text-muted-foreground">
                          {testimonial.role}, {testimonial.company}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  )
}
