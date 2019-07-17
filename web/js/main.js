function ToTableHTML(list) {
    html_string = "";
    for (j = 0; j < list.length; j++) {
        row = list[j];
        html_string += "<tr>";
        for (i = 0; i < row.length; i++) {
            html_string += "<td>" + String(row[i]) + "</td>";
        }
        html_string += "</tr>";
    }
    return html_string;
}
function ToTableHeader(list) {
    html_string = "<tr>";
    for (i = 0; i < list.length; i++) {
        html_string += "<th>" + String(list[i]) + "</th>";
    }
    html_string += "</tr>";
    return html_string;
}
function DatasetAppender(existing, addition) {
    for (i = 0; i < addition.length; i++) {
        if(existing[i]["data"].length >= 1440){ //only use last 2 hours
            existing[i]["data"].shift();
        }
        existing[i]["data"].push(addition[i].data[0]);
    }
    return existing;
}