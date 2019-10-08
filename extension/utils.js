
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

function modifyTransactionReason(reason, person1, person2, charged) {
    let res = '';

    if (charged) {
        if (person1 === 'Arun Srinivas') {
            if (reason.indexOf('ppco') >= 0 || reason.indexOf('pep') >= 0 || reason.indexOf('pepco') >= 0) {
                res = `Pepco Bill - ${person2}`;
            } else if (reason.indexOf('vzon') >= 0 || reason.indexOf('verizon') >= 0) {
                res = `Verizon Bill - ${person2}`;
            } else {
                res = `Paid back by ${person2} for ${reason}`;
            }
        } else {
            res = `Paid back ${person1} for ${reason}`;
        }
    } else { // Means the keyword was paid
        if (person1 === 'Arun Srinivas') {
            res = `Paid back ${person2} for ${reason}`;
        } else {
            if (reason.indexOf('ppco') >= 0 || reason.indexOf('pep') >= 0 || reason.indexOf('pepco') >= 0) {
                res = `Pepco Bill - ${person1}`;
            } else if (reason.indexOf('vzon') >= 0 || reason.indexOf('verizon') >= 0) {
                res = `Verizon Bill - ${person1}`;
            } else {
                res = `Paid back by ${person1} for ${reason}`;
            }
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

        regexp = /<strong>([A-Za-z]+)\s+([A-Za-z]+)<.+<strong>([A-Za-z]+)\s*([A-Za-z]*)</;
        match = regexp.exec(str);
        if (match == null) {
            console.log(str)
        }
        const person1 = match[1] + ' ' + match[2];
        const person2 = match[3] + ' ' + match[4];
        
        regexp = /<\/strong><\/a><span><!-- react-text: \d+ --> <!-- \/react-text --><!-- react-text: \d+ -->(\w+)</;
        match = regexp.exec(str);
        const charged = match[1] === 'charged'; // if true, then person1 CHARGED person2, else, person1 PAID person2

        regexp = /<div class="feed-description__notes__content"><p><!-- react-text: \d+ -->([A-Za-z\d\s\W]*)<!--/
        match = regexp.exec(str);
        let reason = '';
        if (match) {
            reason = match[1]
        }
        reason = modifyTransactionReason(reason.toLowerCase(), person1, person2, charged);

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