const { app, BrowserWindow, ipcMain, BrowserView } = require('electron');
const path = require('path');
const url = require('url');

let mainWindow;
let pdfView; // Add this line at the beginning of the file to store the pdfView instance

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        plugins: true, // Add this line
    });

    const startUrl = process.env.ELECTRON_START_URL || 'http://127.0.0.1:5000';

    mainWindow.loadURL(startUrl);

    mainWindow.on('closed', function () {
        mainWindow = null;
    });

    ipcMain.on('create-pdf-view', (event, pdfURL) => {
        pdfView = new BrowserView({ // Modify this line to store the instance
            webContents: mainWindow.webContents,
        });
        mainWindow.setBrowserView(pdfView);
        pdfView.setBounds({ x: 400, y: 0, width: 400, height: 600 });
        pdfView.webContents.loadURL(pdfURL);
    });


    ipcMain.on('close-pdf-view', () => {
        mainWindow.setBrowserView(null);
        pdfView = null; // Set pdfView to null after removing it
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
