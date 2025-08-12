// Useful when running backend locally on 8000 without Docker
module.exports = {
  server: {
    allowedHosts: ['genai-code-generator.duckdns.org'],
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
}
