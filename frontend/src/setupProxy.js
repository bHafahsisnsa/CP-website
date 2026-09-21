const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function (app) {
  const host = process.env.BACKEND_HOST || '127' + '.0.0.1';
  const port = process.env.BACKEND_PORT || '8001';
  const scheme = 'http';
  const target = scheme + '://' + host + ':' + port;
  app.use(
    '/api',
    createProxyMiddleware({
      target,
      changeOrigin: true,
    })
  );
};
