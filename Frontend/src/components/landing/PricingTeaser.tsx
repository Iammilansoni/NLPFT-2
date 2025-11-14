'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Check, ArrowRight, Sparkles } from 'lucide-react'
import Link from 'next/link'

const plans = [
  {
    name: 'Starter',
    price: '$99',
    period: '/month',
    description: 'Perfect for small teams getting started',
    features: [
      '5 team seats',
      '10,000 test runs/month',
      'Basic templates',
      'Email support',
      'Community access',
    ],
    cta: 'Start Free Trial',
    popular: false,
  },
  {
    name: 'Team',
    price: '$299',
    period: '/month',
    description: 'For growing teams with advanced needs',
    features: [
      '20 team seats',
      '50,000 test runs/month',
      'Advanced templates & versioning',
      'Priority support',
      'SSO integration',
      'Custom datasets',
    ],
    cta: 'Start Free Trial',
    popular: true,
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    period: '',
    description: 'For organizations at scale',
    features: [
      'Unlimited seats',
      'Unlimited test runs',
      'Dedicated infrastructure',
      '24/7 phone support',
      'SLA guarantees',
      'Custom integrations',
      'On-premise deployment',
    ],
    cta: 'Contact Sales',
    popular: false,
  },
]

export function PricingTeaser() {
  const [isDialogOpen, setIsDialogOpen] = useState(false)

  return (
    <>
      <section className="py-20 md:py-32 border-t">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-center mb-16 space-y-4"
          >
            <Badge variant="outline" className="px-4 py-1.5">
              Pricing
            </Badge>
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold font-heading">
              Simple,{' '}
              <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                Transparent Pricing
              </span>
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Start free, scale as you grow. No hidden fees, cancel anytime.
            </p>
          </motion.div>

          <div className="grid gap-8 md:grid-cols-3 max-w-6xl mx-auto">
            {plans.map((plan, index) => (
              <motion.div
                key={plan.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="relative"
              >
                {plan.popular && (
                  <div className="absolute -top-4 left-0 right-0 flex justify-center">
                    <Badge className="bg-gradient-to-r from-primary to-accent text-white border-0">
                      <Sparkles className="mr-1 h-3 w-3" />
                      Most Popular
                    </Badge>
                  </div>
                )}
                
                <Card className={`h-full border-2 ${plan.popular ? 'border-primary shadow-xl scale-105' : 'hover:border-primary/50'} transition-all duration-300`}>
                  <CardHeader className="space-y-4 pb-8">
                    <div>
                      <CardTitle className="text-2xl font-heading">{plan.name}</CardTitle>
                      <CardDescription className="mt-2">{plan.description}</CardDescription>
                    </div>
                    <div className="flex items-baseline gap-1">
                      <span className="text-4xl font-bold font-heading">{plan.price}</span>
                      <span className="text-muted-foreground">{plan.period}</span>
                    </div>
                  </CardHeader>
                  
                  <CardContent className="space-y-6">
                    <ul className="space-y-3">
                      {plan.features.map((feature) => (
                        <li key={feature} className="flex items-start gap-3">
                          <Check className="h-5 w-5 text-success shrink-0 mt-0.5" />
                          <span className="text-sm">{feature}</span>
                        </li>
                      ))}
                    </ul>

                    <Button
                      className="w-full group"
                      variant={plan.popular ? 'default' : 'outline'}
                      size="lg"
                      onClick={() => {
                        if (plan.name === 'Enterprise') {
                          setIsDialogOpen(true)
                        }
                      }}
                      asChild={plan.name !== 'Enterprise'}
                    >
                      {plan.name === 'Enterprise' ? (
                        <>
                          {plan.cta}
                          <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
                        </>
                      ) : (
                        <Link href="/signup">
                          {plan.cta}
                          <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
                        </Link>
                      )}
                    </Button>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="text-center mt-12"
          >
            <p className="text-sm text-muted-foreground">
              All plans include 14-day free trial. No credit card required.{' '}
              <Link href="/pricing" className="text-primary hover:underline font-medium">
                View detailed pricing
              </Link>
            </p>
          </motion.div>
        </div>
      </section>

      {/* Contact Sales Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Contact Enterprise Sales</DialogTitle>
            <DialogDescription>
              Get in touch with our team to discuss custom solutions for your organization.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Work Email</label>
              <input
                type="email"
                placeholder="you@company.com"
                className="w-full px-3 py-2 rounded-lg border bg-background"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Company Name</label>
              <input
                type="text"
                placeholder="Your Company"
                className="w-full px-3 py-2 rounded-lg border bg-background"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Team Size</label>
              <select className="w-full px-3 py-2 rounded-lg border bg-background">
                <option>1-10</option>
                <option>11-50</option>
                <option>51-200</option>
                <option>201-1000</option>
                <option>1000+</option>
              </select>
            </div>
            <Button className="w-full" size="lg">
              Request Demo
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}
