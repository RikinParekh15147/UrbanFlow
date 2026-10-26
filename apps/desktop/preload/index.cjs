const { contextBridge } = require('electron');
contextBridge.exposeInMainWorld('urbanflow', Object.freeze({ version: '1.0.0', desktop: true }));
