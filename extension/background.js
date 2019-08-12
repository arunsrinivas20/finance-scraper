chrome.extension.onConnect.addListener(function(port) {
    port.onMessage.addListener(function(msg) {
         alert(msg)
    });
})