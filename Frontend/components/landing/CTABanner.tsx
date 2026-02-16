'use client'

import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { ArrowRight, Cpu } from 'lucide-react'
import Link from 'next/link'

export function CTABanner() {
  return (
    <section className="py-20 md:py-32 border-t">
      <div className="container mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="relative overflow-hidden rounded-2xl border-2 bg-gradient-to-br from-primary/10 via-background to-accent/10 p-12 md:p-16 text-center"
        >
          {/* Background decoration */}
          <div className="absolute inset-0 -z-10">
            <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-3xl" />
            <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-accent/20 rounded-full blur-3xl" />
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="space-y-6 max-w-3xl mx-auto"
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20">
              <Cpu className="h-4 w-4 text-primary" />
              <span className="text-sm font-medium">Ready to transform your testing?</span>
            </div>

            <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold font-heading">
              Start Testing Smarter,{' '}
              <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                Not Harder
              </span>
            </h2>

            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Join teams who&apos;ve already automated their API testing with natural language.
              No credit card required for your 14-day trial.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
              <Button size="lg" className="group text-base" asChild>
                <Link href="/dashboard">
                  Run a Sample Test
                  <ArrowRight className="ml-2 h-5 w-5 transition-transform group-hover:translate-x-1" />
                </Link>
              </Button>
              <Button size="lg" variant="outline" className="text-base" asChild>
                <Link href="/docs">
                  View Documentation
                </Link>
              </Button>
            </div>

            <p className="text-sm text-muted-foreground pt-4">
              Free trial includes full access to all Team features
            </p>
          </motion.div>
        </motion.div>
      </div>
    </section>
  )
}
