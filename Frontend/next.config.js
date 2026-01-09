/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  experimental: {
    optimizePackageImports: ['lucide-react', 'recharts', 'framer-motion'],
  },
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
      },
      {
        protocol: 'https',
        hostname: 'localhost',
      },
    ],
    formats: ['image/avif', 'image/webp'],
  },
  turbopack: {
    root: '..',
  },
  // API rewrites for backend integration
  // Only add a server-side proxy when BACKEND_INTERNAL_URL is provided.
  // This prevents the dev/build from hardcoding `http://backend:8000` into
  // client-side requests when running the frontend on the host machine.
  async rewrites() {
    const backendBase = process.env.BACKEND_INTERNAL_URL;
    if (!backendBase) {
      return [];
    }
    return [
      {
        source: '/api/:path*',
        destination: `${backendBase}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
