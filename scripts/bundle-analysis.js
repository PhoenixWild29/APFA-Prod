const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
const webpack = require('webpack');
const config = require('../webpack.config.js');

// Add bundle analyzer plugin
config.plugins.push(
  new BundleAnalyzerPlugin({
    analyzerMode: 'static',
    reportFilename: '../reports/bundle-report.html',
    openAnalyzer: true,
    generateStatsFile: true,
    statsFilename: '../reports/bundle-stats.json',
  })
);

// Run webpack with bundle analyzer
webpack(config, (err, stats) => {
  if (err) {
    console.error(err);
    return;
  }

  console.log(
    stats.toString({
      colors: true,
      modules: false,
      children: false,
      chunks: false,
      chunkModules: false,
    })
  );

  if (stats.hasErrors()) {
    console.error('Build failed with errors.');
    process.exit(1);
  }

  console.log('\n✅ Bundle analysis complete!');
  console.log('📊 Report: reports/bundle-report.html');
  console.log('📈 Stats: reports/bundle-stats.json\n');
});

