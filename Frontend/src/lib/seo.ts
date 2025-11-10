import { Metadata } from 'next'

interface SEOProps {
  title: string
  description: string
  path?: string
  image?: string
  noIndex?: boolean
}

const siteConfig = {
  name: 'NLPForge-Tester',
  url: 'https://nlpforge.com',
  ogImage: '/og-image.png',
  description: 'Turn one API hint into full test coverage with AI-powered testing',
  links: {
    twitter: 'https://twitter.com/nlpforge',
    github: 'https://github.com/nlpforge',
  },
}

export function generateSEO({
  title,
  description,
  path = '',
  image,
  noIndex = false,
}: SEOProps): Metadata {
  const url = `${siteConfig.url}${path}`
  const ogImage = image || siteConfig.ogImage

  return {
    title: `${title} | ${siteConfig.name}`,
    description,
    keywords: [
      'API Testing',
      'NLP',
      'AI Testing',
      'Test Automation',
      'Semantic Search',
      'Vector Database',
      'Redis',
      'Machine Learning',
    ],
    authors: [{ name: 'NLPForge Team' }],
    creator: 'NLPForge',
    openGraph: {
      type: 'website',
      locale: 'en_US',
      url,
      title,
      description,
      siteName: siteConfig.name,
      images: [
        {
          url: ogImage,
          width: 1200,
          height: 630,
          alt: title,
        },
      ],
    },
    twitter: {
      card: 'summary_large_image',
      title,
      description,
      images: [ogImage],
      creator: '@nlpforge',
    },
    robots: {
      index: !noIndex,
      follow: !noIndex,
      googleBot: {
        index: !noIndex,
        follow: !noIndex,
        'max-video-preview': -1,
        'max-image-preview': 'large',
        'max-snippet': -1,
      },
    },
    ...(noIndex && {
      metadataBase: new URL(siteConfig.url),
    }),
  }
}

export { siteConfig }
