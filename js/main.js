function ToTableRow(list){
    html_string = "<tr>"
    for (i = 0; i < list.length(); i++) {
        html_string += "<td>"+String(list[i])+"</td>"
    }
    html_string+="</tr>"
    return html_string
}
function ToTableHeader(list){
    html_string = "<tr>"
    for (i = 0; i < list.length(); i++) {
        html_string += "<th>"+String(list[i])+"</th>"
    }
    html_string+="</tr>"
    return html_string
}
function DatasetAppender(existing, addition) {
    for (i = 0; i < addition.length(); i++) {
        existing[i].data.append(addition[i].data[0]);
    }
    return exisiting;
}