var webpack = require('webpack');
var path = require('path');

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
