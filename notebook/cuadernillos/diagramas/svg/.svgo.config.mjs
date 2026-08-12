export default {
  multipass: true,
  plugins: [
    { name: 'preset-default',
      params: { overrides: {
        cleanupIds: false,
        inlineStyles: false,
        minifyStyles: false,
        mergeStyles: false,
        removeUnknownsAndDefaults: false,
        removeUselessStrokeAndFill: false,
        removeHiddenElems: false,
        convertShapeToPath: false,
        mergePaths: false,
      }},
    },
  ],
};
