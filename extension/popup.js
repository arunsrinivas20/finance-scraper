import { parseHTMLArrForTransactionsC1, convertArraytoJSON, parseHTMLArrForTransactionsVenmo } from './utils.js';

function extractVenmoHTMLContent(innerHTML) {
    const beginTransactions = innerHTML.indexOf('<div id="activity-feed">');
    const endRecentTransactions = innerHTML.indexOf('<div class="feed-more">');

    const htmlTransactionString = innerHTML.substring(beginTransactions, endRecentTransactions);

    let htmlArr = htmlTransactionString.split('<div class="feed-story"');
    htmlArr.shift();

    const transactionList = parseHTMLArrForTransactionsVenmo(htmlArr);

    const jsonStringTransactions = convertArraytoJSON(transactionList);

    return jsonStringTransactions;
}

function extractC1HTMLContent(innerHTML) {
    // Add logic to determine the year based on the presence of "Past Transactions"
    // Then use a date object to get the current year

    const beginTransactions = innerHTML.indexOf('<div class="container bank-ledger"');
    const endRecentTransactions = innerHTML.indexOf('View More Transactions');

    const htmlTransactionString = innerHTML.substring(beginTransactions, endRecentTransactions);
    let htmlArr = htmlTransactionString.split(/id="transaction-\d+"/);
    htmlArr.shift();

    const transactionList = parseHTMLArrForTransactionsC1(htmlArr);

    const jsonStringTransactions = convertArraytoJSON(transactionList);

    return jsonStringTransactions;
}

function sendPageHTMLContent(innerHTML, tab, filePath, excelSheet, email) {
    const tabTitle = tab.title;
    let jsonStringTransactions = undefined;

    if (tabTitle.indexOf('Capital One') >= 0) {
        jsonStringTransactions = extractC1HTMLContent(innerHTML);
    } else if (tabTitle.indexOf('Venmo') >= 0) {
        jsonStringTransactions = extractVenmoHTMLContent(innerHTML);
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
    xmlhttp.send('data=' + jsonStringTransactions + '&financial_institution=' + tab.title + '&file_path=' + filePath + '&excel_sheet=' + excelSheet + '&email=' + email);

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