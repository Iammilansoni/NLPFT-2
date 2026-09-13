'use client'

import { motion } from 'framer-motion'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  FileCode, 
  TrendingUp, 
  Filter, 
  Target,
  Code2,
  Layers
} from 'lucide-react'

const features = [
  {
    icon: FileCode,
    title: 'Auto-Templates & Versioning',
    description: 'Intelligent template generation with built-in version control. Track changes, rollback easily, and maintain test consistency across environments.',
    badge: 'Smart',
    code: `template: {
  version: "2.1.0",
  intent: "login",
  auto_generated: true
}`,
  },
  {
    icon: TrendingUp,
    title: 'Incremental Dataset Enrichment',
    description: 'Continuously improve test coverage with AI-powered dataset expansion. Learn from production patterns and edge cases automatically.',
    badge: 'Adaptive',
    code: `enrichment: {
  new_patterns: 47,
  confidence: 0.94,
  auto_approved: 38
}`,
  },
  {
    icon: Filter,
    title: 'Redis Vector + Filters',
    description: 'Lightning-fast semantic search with advanced filtering. Combine vector similarity with metadata queries for precise test matching.',
    badge: 'Fast',
    code: `search({
  query: "auth flow",
  filters: { env: "prod" },
  top_k: 5
})`,
  },
  {
    icon: Target,
    title: 'Confidence Scoring',
    description: 'Transparent explainability for every test match. Understand why tests were selected and validate AI decisions with detailed confidence metrics.',
    badge: 'Transparent',
    code: `result: {
  confidence: 0.96,
  factors: ["intent", "entities"],
  explanation: "High semantic match"
}`,
  },
]

export function FeatureHighlights() {
  return (
    <section className="relative py-12 md:py-16 border-t overflow-hidden">
      {/* Animated background */}
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
          className="absolute top-1/4 right-1/4 w-96 h-96 bg-accent/20 rounded-full blur-3xl"
        />
      </div>
      
      <div className="container mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-center mb-16 space-y-4"
        >
          <Badge variant="outline" className="px-4 py-1.5">
            Feature Highlights
          </Badge>
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold font-heading">
            Built for{' '}
            <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              Production Scale
            </span>
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Enterprise-grade features that grow with your testing needs
          </p>
        </motion.div>

        <div className="grid gap-8 md:grid-cols-2">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 30, scale: 0.95 }}
              whileInView={{ opacity: 1, y: 0, scale: 1 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.6, delay: index * 0.1, ease: [0.22, 1, 0.36, 1] }}
            >
              <Card className="h-full border-2 hover:border-primary/50 transition-all duration-300 hover:shadow-glow group overflow-hidden glass-card">
                {/* Animated gradient overlay */}
                <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500">
                  <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-accent/10" />
                </div>
                
                <CardHeader className="space-y-5 relative z-10">
                  <div className="flex items-start justify-between">
                    <motion.div 
                      className="h-14 w-14 rounded-2xl bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center shadow-soft"
                      whileHover={{ scale: 1.1, rotate: 5 }}
                      transition={{ type: "spring", stiffness: 400 }}
                    >
                      <feature.icon className="h-7 w-7 text-primary" />
                    </motion.div>
                    <Badge className="bg-gradient-to-r from-primary/10 to-accent/10 border-primary/30 text-primary font-semibold">
                      {feature.badge}
                    </Badge>
                  </div>
                  <CardTitle className="text-2xl font-heading group-hover:text-primary transition-colors">
                    {feature.title}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-5 relative z-10">
                  <p className="text-muted-foreground leading-relaxed text-base">
                    {feature.description}
                  </p>
                  
                  {/* Enhanced Code snippet */}
                  <div className="relative group/code">
                    <div className="absolute inset-0 bg-gradient-to-r from-primary/20 to-accent/20 rounded-xl blur-xl opacity-0 group-hover/code:opacity-100 transition-opacity duration-500" />
                    <div className="relative p-5 rounded-xl bg-card/80 backdrop-blur-sm border-2 border-border group-hover/code:border-primary/30 font-mono text-xs overflow-x-auto transition-colors shadow-soft">
                      <div className="flex items-center gap-2 mb-3 pb-2 border-b border-border/50">
                        <div className="flex gap-1.5">
                          <div className="h-2.5 w-2.5 rounded-full bg-red-500/60" />
                          <div className="h-2.5 w-2.5 rounded-full bg-yellow-500/60" />
                          <div className="h-2.5 w-2.5 rounded-full bg-green-500/60" />
                        </div>
                        <span className="text-xs text-muted-foreground ml-2">example.ts</span>
                      </div>
                      <pre className="text-foreground/90">
                        <code>{feature.code}</code>
                      </pre>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        {/* Additional features grid */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="mt-16 grid gap-6 md:grid-cols-3"
        >
          {[
            { icon: Code2, title: 'REST & GraphQL', desc: 'Full API protocol support' },
            { icon: Layers, title: 'Multi-Environment', desc: 'Dev, staging, production' },
            { icon: Target, title: 'Data Masking', desc: 'PII protection built-in' },
          ].map((item, i) => (
            <motion.div
              key={item.title}
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.3, delay: 0.5 + i * 0.1 }}
            >
              <Card className="border hover:border-primary/50 transition-colors duration-300">
                <CardContent className="p-6 flex items-start gap-4">
                  <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                    <item.icon className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <h4 className="font-semibold mb-1">{item.title}</h4>
                    <p className="text-sm text-muted-foreground">{item.desc}</p>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  )
}
