var webpack = require('webpack');
var path = require('path');

process.env.VUE_APP_PREVENT_SIGNUPS = process.env.PREVENT_SIGNUPS ? true : '';

module.exports = {
  lintOnSave: false,
  outputDir: path.resolve(__dirname, '../dist'),
  assetsDir: 'static',
  devServer: {
    proxy: {
      '^/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
    }
  },
  configureWebpack: {
    plugins: [
      new webpack.ContextReplacementPlugin(
        /date\-fns[\/\\]/,
        new RegExp('[/\\\\\](en)[/\\\\\]')
      )
    ]
  }
};
