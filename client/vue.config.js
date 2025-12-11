var webpack = require('webpack');
var path = require('node:path');

process.env.VUE_APP_PREVENT_SIGNUPS = process.env.PREVENT_SIGNUPS ? 'true' : '';
process.env.VUE_APP_BASE_URL = process.env.BASE_URL ? process.env.BASE_URL : '';
process.env.VUE_APP_VERSION = process.env.APP_VERSION || 'dev';

module.exports = {
  lintOnSave: false,
  outputDir: path.resolve(__dirname, '../dist'),
  assetsDir: 'static',
  devServer: {
    proxy: {
      '^/api/events/stream': {
        target: 'http://localhost:5001',
        changeOrigin: true,
        // SSE-specific settings to prevent buffering
        headers: {
          Connection: 'keep-alive',
        },
        onProxyReq: (proxyReq, req, res) => {
          // Disable request buffering
          proxyReq.setHeader('Cache-Control', 'no-cache');
        },
        onProxyRes: (proxyRes, req, res) => {
          // Ensure streaming response is not buffered
          proxyRes.headers['cache-control'] = 'no-cache';
          proxyRes.headers['x-accel-buffering'] = 'no';
        },
      },
      '^/api': {
        target: 'http://localhost:5001',
        changeOrigin: true,
      },
      '^/uploads': {
        target: 'http://localhost:5001',
        changeOrigin: true,
      },
    },
  },
  configureWebpack: {
    plugins: [new webpack.ContextReplacementPlugin(/date-fns[/\\]/, /[/\\](en)[/\\]/)],
  },
  css: {
    loaderOptions: {
      sass: {
        sassOptions: {
          api: 'modern',
          silenceDeprecations: [
            'legacy-js-api',
            'import',
            'global-builtin',
            'color-functions',
            'slash-div',
          ],
        },
      },
    },
  },
};
