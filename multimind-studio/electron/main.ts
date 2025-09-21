import { app, BrowserWindow, session } from 'electron';
import path from 'path';
import { ChildProcessWithoutNullStreams, spawn } from 'child_process';

const isDev = process.env.NODE_ENV === 'development';
let backendProcess: ChildProcessWithoutNullStreams | null = null;

const startBackend = () => {
  if (isDev || backendProcess) {
    return;
  }
  const pythonExecutable = process.env.PYTHON_PATH || 'python';
  const backendDir = path.resolve(__dirname, '../app/backend');
  backendProcess = spawn(
    pythonExecutable,
    ['-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', '8765'],
    {
      cwd: backendDir,
      env: { ...process.env },
      stdio: 'inherit',
    }
  );
};

const stopBackend = () => {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
};

const setupProxy = () => {
  const filter = { urls: ['*://*/*'] };
  session.defaultSession.webRequest.onBeforeRequest(filter, (details, callback) => {
    try {
      const requestUrl = new URL(details.url);
      if (requestUrl.pathname.startsWith('/api') && requestUrl.host !== 'localhost:8765') {
        const redirectURL = `http://localhost:8765${requestUrl.pathname}${requestUrl.search}`;
        callback({ redirectURL });
        return;
      }
    } catch (error) {
      // ignore malformed URLs
    }
    callback({});
  });
};

const createWindow = async () => {
  const mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      preload: path.resolve(__dirname, 'preload.ts'),
    },
  });

  setupProxy();

  if (isDev) {
    await mainWindow.loadURL('http://localhost:5173');
  } else {
    const indexPath = path.resolve(__dirname, '../app/frontend/dist/index.html');
    await mainWindow.loadFile(indexPath);
  }
};

app.whenReady().then(() => {
  startBackend();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    stopBackend();
    app.quit();
  }
});

app.on('quit', () => {
  stopBackend();
});
