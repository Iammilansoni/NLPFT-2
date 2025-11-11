import type { Metadata } from 'next'
import { Inter, Manrope } from 'next/font/google'
import '@/styles/globals.css'
import { ThemeProvider } from '@/lib/theme-provider'
import { QueryProvider } from '@/lib/query-provider'
import { Toaster } from '@/components/ui/toaster'
import { ConditionalNav } from '@/components/ConditionalNav'
import { SidebarProvider } from '@/contexts/sidebar-context'
import { LayoutContent } from '@/components/layout-content'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
})

const manrope = Manrope({
  subsets: ['latin'],
  variable: '--font-manrope',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'NLPForge - AI-Powered API Testing Platform',
  description: 'Transform natural language into production-ready API tests. Generate datasets, execute tests, and analyze results with semantic understanding.',
  keywords: ['API Testing', 'NLP', 'AI', 'Test Automation', 'Semantic Search'],
  authors: [{ name: 'NLPForge Team' }],
  openGraph: {
    title: 'NLPForge - AI-Powered API Testing',
    description: 'Transform natural language into production-ready API tests',
    type: 'website',
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning className={`${inter.variable} ${manrope.variable}`}>
      <body className="min-h-screen bg-background font-sans antialiased" suppressHydrationWarning>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <QueryProvider>
            <SidebarProvider>
              <ConditionalNav />
              <LayoutContent>{children}</LayoutContent>
              <Toaster />
            </SidebarProvider>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
