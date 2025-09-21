import { contextBridge } from 'electron';

contextBridge.exposeInMainWorld('multimind', {
  platform: process.platform,
  nodeVersion: process.version,
});
