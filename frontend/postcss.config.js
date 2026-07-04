// PostCSS transforms our CSS at build time. Tailwind and autoprefixer
// are plugins in that pipeline: Tailwind generates utility classes,
// autoprefixer adds browser-compatibility prefixes automatically.
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
