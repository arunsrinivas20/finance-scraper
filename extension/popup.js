function extractHTMLContent(innerHTML) {
    const beginTransactions = innerHTML.indexOf('<div id="activity-feed">');

    let htmlTransactionString = innerHTML.substring(beginTransactions);
    htmlTransactionString = htmlTransactionString.replace(/&/g, "")

    return htmlTransactionString;
}

function sendPageHTMLContent(innerHTML, tab, filePath, excelSheet, email) {
    const tabTitle = tab.title;
    let stringOfTransactions = undefined;

    if (tabTitle.indexOf('Capital One') >= 0) {
        stringOfTransactions = '' + extractHTMLContent(innerHTML, '<div class="container bank-ledger"');
    } else if (tabTitle.indexOf('Venmo') >= 0) {
        stringOfTransactions = '' + extractHTMLContent(innerHTML, '<div id="activity-feed">');
        console.log(stringOfTransactions)
        console.log(stringOfTransactions.length)
    }

    let xmlhttp = new XMLHttpRequest();

    xmlhttp.onreadystatechange = function() {
        if (xmlhttp.readyState === XMLHttpRequest.DONE) {
            let port = chrome.extension.connect({
                name: "Communication"
            });
            port.postMessage(xmlhttp.response);
        } 
    };

    xmlhttp.open("POST", "http://127.0.0.1:5000/", true);
    xmlhttp.setRequestHeader('content-type', 'application/x-www-form-urlencoded;charset=UTF-8');
    xmlhttp.send('data=' + stringOfTransactions + '&financial_institution=' + tabTitle + '&file_path=' + filePath + '&excel_sheet=' + excelSheet + '&email=' + email);

    console.log(xmlhttp);
}

document.addEventListener('DOMContentLoaded', () => {
    let checkPageButton = document.getElementById('checkPage');
    checkPageButton.addEventListener('click', async () => {
        await chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
            let tab = tabs[0];
            let filePath = document.getElementById('inputFilePath').value;
            let excelSheet = document.getElementById('inputExcelSheet').value;

            chrome.tabs.executeScript({
                code: '(' + function() {
                    return {
                        innerHTML: document.body.innerHTML};
                    } + ')();'
                }, function(results) {
                    sendPageHTMLContent(results[0].innerHTML, tab, filePath, excelSheet, undefined);
            });
      });
    }, false);
}, false);

document.addEventListener('DOMContentLoaded', () => {
    let checkPageEmailButton = document.getElementById('checkPageEmail');
    checkPageEmailButton.addEventListener('click', async () => {
        await chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
            let tab = tabs[0];
            let email = document.getElementById('inputEmail').value;

            chrome.tabs.executeScript({
                code: '(' + function() {
                    return {
                        innerHTML: document.body.innerHTML};
                    } + ')();'
                }, function(results) {
                    sendPageHTMLContent(results[0].innerHTML, tab, undefined, undefined, email);
            });
      });
    }, false);
}, false);