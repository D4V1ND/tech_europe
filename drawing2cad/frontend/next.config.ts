import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      { source: '/api/:path*', destination: 'http://localhost:5001/api/:path*' },
      { source: '/runs/:path*', destination: 'http://localhost:5001/runs/:path*' },
    ]
  },
}

export default nextConfig
