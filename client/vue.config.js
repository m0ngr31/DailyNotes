var webpack = require('webpack');
var path = require('node:path');

process.env.VUE_APP_PREVENT_SIGNUPS = process.env.PREVENT_SIGNUPS ? 'true' : '';
process.env.VUE_APP_BASE_URL = process.env.BASE_URL ? process.env.BASE_URL : '';

module.exports = {
  lintOnSave: false,
  outputDir: path.resolve(__dirname, '../dist'),
  assetsDir: 'static',
  devServer: {
    proxy: {
      '^/api': {
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
