'use client'

import { motion } from 'framer-motion'
import { Badge } from '@/components/ui/badge'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'

const faqs = [
  {
    question: 'How does NLPForge handle sensitive data and PII?',
    answer: 'We implement automatic PII detection and masking at the ingestion layer. All sensitive data is encrypted at rest and in transit using AES-256. Our data masking engine supports custom rules and complies with GDPR, HIPAA, and SOC 2 requirements.',
  },
  {
    question: 'What are the rate limits for API testing?',
    answer: 'Rate limits vary by plan: Starter (100 req/min), Team (500 req/min), Enterprise (custom). We use intelligent throttling to prevent overwhelming your APIs while maximizing test throughput. Burst capacity is available for all plans.',
  },
  {
    question: 'Can I use NLPForge in a multi-tenant environment?',
    answer: 'Yes, NLPForge is built for multi-tenancy from the ground up. Each tenant has isolated data stores, separate vector embeddings, and independent access controls. Enterprise plans support custom tenant configurations and white-labeling.',
  },
  {
    question: 'How do I export test results and reports?',
    answer: 'Export options include JSON, CSV, and PDF formats via our REST API or dashboard. We also support webhooks for real-time result streaming and integrations with popular tools like Slack, Jira, and DataDog.',
  },
  {
    question: 'What kind of support do you provide?',
    answer: 'Starter plans include email support (24-hour response). Team plans get priority support with 4-hour response times. Enterprise customers receive 24/7 phone support, dedicated success managers, and custom SLAs.',
  },
  {
    question: 'Can I run NLPForge on-premise or in my own cloud?',
    answer: 'Enterprise plans support on-premise deployment and private cloud installations (AWS, Azure, GCP). We provide Docker containers, Kubernetes manifests, and full deployment assistance. Air-gapped environments are supported.',
  },
]

export function FAQ() {
  return (
    <section className="py-20 md:py-32 bg-muted/30 border-t">
      <div className="container mx-auto px-4 max-w-4xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-center mb-16 space-y-4"
        >
          <Badge variant="outline" className="px-4 py-1.5">
            FAQ
          </Badge>
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold font-heading">
            Frequently Asked{' '}
            <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              Questions
            </span>
          </h2>
          <p className="text-lg text-muted-foreground">
            Everything you need to know about NLPForge-Tester
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <Accordion type="single" collapsible className="space-y-4">
            {faqs.map((faq, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.3, delay: 0.3 + index * 0.05 }}
              >
                <AccordionItem
                  value={`item-${index}`}
                  className="border-2 rounded-lg px-6 bg-card hover:border-primary/50 transition-colors duration-300"
                >
                  <AccordionTrigger className="text-left font-semibold hover:no-underline py-5">
                    {faq.question}
                  </AccordionTrigger>
                  <AccordionContent className="text-muted-foreground leading-relaxed pb-5">
                    {faq.answer}
                  </AccordionContent>
                </AccordionItem>
              </motion.div>
            ))}
          </Accordion>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.6 }}
          className="text-center mt-12"
        >
          <p className="text-muted-foreground">
            Still have questions?{' '}
            <a href="/contact" className="text-primary hover:underline font-medium">
              Contact our team
            </a>
          </p>
        </motion.div>
      </div>
    </section>
  )
}
