
const monthToNum = {
    'Jan': 1,
    'Feb': 2,
    'Mar': 3,
    'Apr': 4,
    'May': 5,
    'Jun': 6,
    'Jul': 7,
    'Aug': 8,
    'Sep': 9,
    'Oct': 10,
    'Nov': 11,
    'Dec': 12,
    'January': 1,
    'February': 2,
    'March': 3,
    'April': 4,
    'May': 5,
    'June': 6,
    'July': 7,
    'August': 8,
    'September': 9,
    'October': 10,
    'November': 11,
    'December': 12
}

export function convertArraytoJSON(transactionArr) {
    let res = {};
    const len = transactionArr.length;

    for (let i = 0; i < len; i++) {
        res['' + i] = transactionArr[i];
    }

    return JSON.stringify(res);
}

export function parseHTMLArrForTransactionsC1(htmlArr) {
    let res = []

    htmlArr.map(str => {
        let regexp = /class="month">([A-Za-z]+)</;
        let match = regexp.exec(str);
        const month = match[1];

        regexp = /class="day">(\d+)</;
        match = regexp.exec(str);
        const day = match[1];

        regexp = /class="italic">([A-Za-z,:;\-\d.?"'{}\[\]\s!@#$%^&*()+=]+)</;
        match = regexp.exec(str);
        const desc = match[1];

        regexp = /class="transaction-amount ([A-Za-z]*)">\$([\d,]+\.\d+)</;
        match = regexp.exec(str);
        const isDebit = match[1].toLowerCase() === 'debit'
        let amount = isDebit ? '-' : ''
        amount += match[2]

        regexp = /class="transaction-balance">\$([\d,]+\.\d+)</;
        match = regexp.exec(str);
        const balance = match[1];

        res.push({
            date: monthToNum[month] + '/' + day + '/19',
            description: desc,
            amount: amount,
            balance: balance
        })
    })

    return res;
}

function modifyTransactionReason(reason, person, requested) {
    let res = '';

    if (reason.indexOf('ppco') >= 0 || reason.indexOf('pep') >= 0) {
        res = `Pepco Bill - ${person}`;
    } else if (reason.indexOf('vzon') >= 0) {
        res = `Verizon Bill - ${person}`;
    } else {
        if (requested) {
            res = `Paid back ${person} for ${reason}`;
        } else {
            res = `Paid back by ${person} for ${reason}`;
        }   
    }

    return res;
}

export function parseHTMLArrForTransactionsVenmo(htmlArr) {
    let res = []
    htmlArr.map(str => {
        let regexp = /<span class="feed-description__notes__meta"><span>([A-Za-z]+)\s+(\d+),\s+(\d+),\s+\d+:\d+\s+[A-Z]{2}</;
        let match = regexp.exec(str);
        const month = match[1];
        const day = match[2];
        const year = match[3].substring(2);

        regexp = /<strong>([A-Za-z]+)\s+([A-Za-z]+)<.+<strong>([A-Za-z]+)\s+([A-Za-z]+)</;
        match = regexp.exec(str);
        const person1 = match[1] + ' ' + match[2];
        const person2 = match[3] + ' ' + match[4];
        const transactionPartner = person1 !== 'Arun Srinivas' ? person1 : person2;
        regexp = /<div class="feed-description__notes__content"><p><!-- react-text: \d+ -->([A-Za-z\d\s\W]*)<!--/
        match = regexp.exec(str);
        let reason = match[1];
        reason = modifyTransactionReason(reason.toLowerCase(), transactionPartner, transactionPartner === person1);

        regexp = /<div class="feed-description__amount"><span class="[A-Za-z]*">(-?)\$([\d,]+\.\d+)</
        match = regexp.exec(str);
        let amount = match[1] + match[2]

        // Maybe think about how to do the category

        res.push({
            date: monthToNum[month] + '/' + day + '/' + year,
            description: reason,
            amount: amount
        })
    })

    return res;
}