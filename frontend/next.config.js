/** @type {import('next').NextConfig} */

const nextConfig = {
    env: {
        NEXT_PUBLIC_FEEDS_URL: "http://localhost",
        NEXT_PUBLIC_FEEDS_PORT: "3010"
    }
}

module.exports = nextConfig
