function validateForm() {
var elements = document.getElementsByTagName("input")
var finalResult=true
for (var i = 0; i < elements.length; i++) {
    //if (elements[i].value == "" & elements[i].attributes.required=="required") {
    if (elements[i].value == "") {
        for (var l = 0; l < elements[i].attributes.length;l++) {
          console.log(elements[i].attributes[l]);
        }
        finalResult=false
    }
}
return finalResult;
}

function confirmSubmission() {
  confirm("Are you sure you wish to submit this request?");
}
