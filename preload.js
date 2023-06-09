const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electron', {
    createPDFView: (pdfURL) => {
        ipcRenderer.send('create-pdf-view', pdfURL);
    },
    closePDFView: () => {
        ipcRenderer.send('close-pdf-view');
    },
});

