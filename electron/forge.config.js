const path = require('node:path');
const { FusesPlugin } = require('@electron-forge/plugin-fuses');
const { FuseV1Options, FuseVersion } = require('@electron/fuses');

const icon = path.join(__dirname, 'assets', 'icon');
const iconPng = path.join(__dirname, 'assets', 'icon.png');
const iconIco = path.join(__dirname, 'assets', 'icon.ico');

module.exports = {
  packagerConfig: {
    asar: true,
    name: 'Motion Base',
    executableName: 'motion-base',
    appBundleId: 'top.tlcfem.motion-base',
    appCategoryType: 'public.app-category.education',
    appCopyright: 'Copyright © 2022-2026 Theodore Chang',
    icon,
    win32metadata: {
      CompanyName: 'Theodore Chang',
      FileDescription: 'Motion Base strong-motion database',
      ProductName: 'Motion Base',
      InternalName: 'motion-base',
      OriginalFilename: 'motion-base.exe',
    },
  },
  rebuildConfig: {},
  makers: [
    {
      name: '@electron-forge/maker-squirrel',
      config: {
        name: 'motion_base',
        authors: 'Theodore Chang',
        description: 'Desktop shell for the Motion Base strong-motion database',
        setupIcon: iconIco,
      },
    },
    {
      name: '@electron-forge/maker-zip',
      platforms: ['darwin', 'win32', 'linux'],
    },
    {
      name: '@electron-forge/maker-deb',
      config: {
        options: {
          maintainer: 'Theodore Chang <tlcfem@gmail.com>',
          homepage: 'https://github.com/TLCFEM/motion-base',
          icon: iconPng,
          categories: ['Education', 'Science'],
        },
      },
    },
    {
      name: '@electron-forge/maker-rpm',
      config: {
        options: {
          homepage: 'https://github.com/TLCFEM/motion-base',
          license: 'GPL-3.0-or-later',
          icon: iconPng,
        },
      },
    },
  ],
  plugins: [
    {
      name: '@electron-forge/plugin-auto-unpack-natives',
      config: {},
    },
    // Fuses are used to enable/disable various Electron functionality
    // at package time, before code signing the application
    new FusesPlugin({
      version: FuseVersion.V1,
      [FuseV1Options.RunAsNode]: false,
      [FuseV1Options.EnableCookieEncryption]: true,
      [FuseV1Options.EnableNodeOptionsEnvironmentVariable]: false,
      [FuseV1Options.EnableNodeCliInspectArguments]: false,
      [FuseV1Options.EnableEmbeddedAsarIntegrityValidation]: true,
      [FuseV1Options.OnlyLoadAppFromAsar]: true,
    }),
  ],
};
