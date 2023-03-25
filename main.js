const { app, BrowserWindow, ipcMain, BrowserView } = require('electron');
const path = require('path');
const url = require('url');

let mainWindow;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            nodeIntegration: true
        },
        plugins: true, // Add this line
    });

    const startUrl = process.env.ELECTRON_START_URL || 'http://127.0.0.1:5000';

    mainWindow.loadURL(startUrl);


    mainWindow.on('closed', function () {
        mainWindow = null;
    });
}

app.on('ready', createWindow);

app.on('window-all-closed', function () {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', function () {
    if (mainWindow === null) {
        createWindow();
    }
});
