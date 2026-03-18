/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
}

// Add signal handler for clean shutdown
if (process.platform !== 'win32') {
  process.on('SIGINT', () => {
    console.log('\n[Frontend] Shutting down gracefully...')
    process.exit(0)
  })
  
  process.on('SIGTERM', () => {
    console.log('\n[Frontend] Shutting down gracefully...')
    process.exit(0)
  })
}

module.exports = nextConfig
