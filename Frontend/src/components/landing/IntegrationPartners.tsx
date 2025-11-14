"use client";
import { Card } from "@/components/ui/card";
import { Database, Server, Cloud, Code, GitBranch, Terminal, Cpu, Network } from "lucide-react";

export function IntegrationPartners() {
  return (
    <section className="py-24 theme-transition">
      <div className="mx-auto max-w-7xl">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 rounded-full border border-cyan-200/50 dark:border-cyan-400/30 bg-white/90 dark:bg-slate-800/90 px-6 py-2.5 text-sm font-medium tracking-wide backdrop-blur-md shadow-lg mb-6">
            <Network className="h-4 w-4 text-cyan-600 dark:text-cyan-400 animate-pulse" />
            <span className="text-cyan-900 dark:text-cyan-100 font-semibold">Seamless Integration</span>
          </div>
          
          <h2 className="text-4xl md:text-5xl font-bold tracking-tight mb-6">
            <span className="bg-gradient-to-r from-cyan-600 via-blue-600 to-indigo-600 dark:from-cyan-400 dark:via-blue-400 dark:to-indigo-400 bg-clip-text text-transparent">
              Integrates With Your Stack
            </span>
          </h2>
          
          <p className="text-xl text-muted max-w-3xl mx-auto leading-relaxed">
            NLPForge works seamlessly with your existing tools, databases, and infrastructure—no migration required.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {integrationCategories.map((category, index) => (
            <Card 
              key={category.title}
              className="p-6 glass-morphism border-2 hover:border-cyan-500/50 dark:hover:border-cyan-400/50 shadow-xl hover:shadow-2xl transition-all duration-300 group"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="text-center">
                <div 
                  className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-4 shadow-lg group-hover:scale-110 transition-transform"
                  style={{
                    background: `linear-gradient(135deg, ${category.color}20, ${category.color}35)`
                  }}
                >
                  <category.icon 
                    className="h-8 w-8" 
                    style={{ color: category.color }}
                  />
                </div>
                
                <h3 className="text-lg font-bold mb-3 group-hover:text-cyan-600 dark:group-hover:text-cyan-400 transition-colors">
                  {category.title}
                </h3>
                
                <ul className="space-y-2">
                  {category.items.map((item) => (
                    <li key={item} className="text-sm text-muted">
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            </Card>
          ))}
        </div>

        <div className="relative">
          <div className="text-center mb-8">
            <p className="text-lg font-semibold text-muted">Trusted by teams using</p>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-8">
            {techStack.map((tech, index) => (
              <div 
                key={tech.name}
                className="flex items-center justify-center p-4 rounded-xl glass-light hover:glass-medium transition-all duration-300 group cursor-pointer"
                style={{ animationDelay: `${index * 50}ms` }}
                title={tech.name}
              >
                <div className="text-center">
                  <div 
                    className="w-12 h-12 rounded-lg flex items-center justify-center mx-auto mb-2 group-hover:scale-110 transition-transform"
                    style={{ 
                      background: `linear-gradient(135deg, ${tech.color}15, ${tech.color}25)` 
                    }}
                  >
                    <tech.icon 
                      className="h-6 w-6" 
                      style={{ color: tech.color }}
                    />
                  </div>
                  <p className="text-xs font-medium text-muted group-hover:text-foreground transition-colors">
                    {tech.name}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-16 p-8 rounded-2xl glass-morphism border-2 border-cyan-500/30 dark:border-cyan-400/30">
          <div className="flex flex-col md:flex-row items-center gap-6">
            <div className="flex-shrink-0">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-xl">
                <Code className="h-10 w-10 text-white" />
              </div>
            </div>
            <div className="flex-1 text-center md:text-left">
              <h3 className="text-2xl font-bold mb-2">RESTful API & SDKs</h3>
              <p className="text-muted leading-relaxed">
                Integrate NLPForge into your existing workflows with our comprehensive API. Available SDKs for Python, JavaScript, Java, and more.
              </p>
            </div>
            <div className="flex-shrink-0">
              <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-100 dark:bg-cyan-900/30 border border-cyan-300 dark:border-cyan-700">
                <Terminal className="h-5 w-5 text-cyan-700 dark:text-cyan-400" />
                <code className="text-sm font-mono text-cyan-800 dark:text-cyan-300">npm install nlpforge</code>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

const integrationCategories = [
  {
    title: 'Databases',
    icon: Database,
    color: '#3b82f6', 
    items: ['PostgreSQL', 'MySQL', 'MongoDB', 'Redis']
  },
  {
    title: 'Cloud Platforms',
    icon: Cloud,
    color: '#10b981', 
    items: ['AWS', 'Azure', 'GCP', 'Heroku']
  },
  {
    title: 'CI/CD Tools',
    icon: GitBranch,
    color: '#8b5cf6', 
    items: ['GitHub Actions', 'Jenkins', 'CircleCI', 'GitLab']
  },
  {
    title: 'Monitoring',
    icon: Server,
    color: '#f59e0b', 
    items: ['Prometheus', 'Grafana', 'DataDog', 'New Relic']
  }
];

const techStack = [
  { name: 'Node.js', icon: Cpu, color: '#10b981' },
  { name: 'Python', icon: Code, color: '#3b82f6' },
  { name: 'Docker', icon: Server, color: '#06b6d4' },
  { name: 'Kubernetes', icon: Network, color: '#8b5cf6' },
  { name: 'PostgreSQL', icon: Database, color: '#3b82f6' },
  { name: 'MongoDB', icon: Database, color: '#10b981' },
  { name: 'Redis', icon: Database, color: '#ef4444' },
  { name: 'GraphQL', icon: Code, color: '#ec4899' }
];
