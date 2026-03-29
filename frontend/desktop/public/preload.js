const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  platform: process.platform,
  nodeVersion: process.versions.node,
  electronVersion: process.versions.electron
});
