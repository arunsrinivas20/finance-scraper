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