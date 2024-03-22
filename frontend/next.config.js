/** @type {import('next').NextConfig} */

// const nextConfig = {
//     env: {
//         NEXT_PUBLIC_FEEDS_URL: "http://localhost",
//         NEXT_PUBLIC_FEEDS_PORT: "3010"
//     }
// }

// module.exports = nextConfig

module.exports = {
    async rewrites() {
      return [
        {
          source: '/api/:path*',
          destination: 'http://127.0.0.1:3010/:path*', // Proxy to Backend
        },
      ]
    },
  }