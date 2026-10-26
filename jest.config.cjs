// The shell's own code; the website's app.js is tested in frontend/wallet.
module.exports = {
  testEnvironment: "jsdom",
  transform: {
    "^.+\\.ts$": [
      "ts-jest",
      { tsconfig: { esModuleInterop: true, resolveJsonModule: true, module: "commonjs" } },
    ],
  },
  testMatch: ["<rootDir>/tests/**/*.test.ts"],
  collectCoverageFrom: ["capacitor.config.ts", "www/offline.js"],
  coverageThreshold: {
    global: { statements: 100, branches: 100, functions: 100, lines: 100 },
  },
  coverageReporters: ["text"],
};
