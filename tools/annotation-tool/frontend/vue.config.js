module.exports = {
    devServer: {
        proxy: "http://0.0.0.0:5000"
      },
      publicPath: process.env.NODE_ENV === 'production'
      ? '/static/'
      : '/'
}
