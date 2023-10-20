function ping(myURL){
  return $.ajax({
    url: myURL,
    async: false
  });
}

function socketLookup(myURL){
  return $.ajax({
    url: myURL,
    async: false
  });
}

function checkBadNames(mything) {
   if (mything.includes("127.0.0.1") || mything.includes("localhost")) {
      return true;
    }
  return false;
}
function isEmptyOrSpaces(str){
    return str === null || str.match(/^ *$/) !== null;
}

function validateForm() {
   var dnsValue = document.getElementsByName('extravardnsRecordValue')[0].value.toLowerCase();
   var dnsRecordFQDN = document.getElementsByName('extravardnsRecordFQDN')[0].value.toLowerCase();
   var selectionValue = document.getElementsByName('extravardnsRecordType')[0].value;
   var viewType = document.getElementsByName('extravardnsRecordView')[0].value;
   var SNOWapp = document.getElementsByName('extravardnsRecordApplication')[0].value.toLowerCase();
   var dnsRecordSCTASK = document.getElementsByName('extravardnsRecordSCTASK')[0].value.toLowerCase();
   var e = document.getElementById("extravardnsCreatePTR");
   var value = e.options[e.selectedIndex].value;
   var extravardnsCreatePTR = e.options[e.selectedIndex].text;
   var myresults=true;
   var tosay="";
   var socketRez=socketLookup("/socketlookup?address="+dnsValue);
   var socketJSON=JSON.parse(socketRez.responseText)
   var regEx = /^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
   if (dnsRecordFQDN.includes("dir.health") && (viewType=="Internal" || viewType =="Both")) {
      tosay=tosay+"\ndir.health entries for the Internal view are not managed by Infoblox at this time.";
      myresults=false;
   }
   if (selectionValue == "PTR" || (selectionValue=="A" && extravardnsCreatePTR == "yes")) {
     if (dnsValue.startsWith("10.146.")||dnsValue.startsWith("10.148.")) {
       tosay=tosay+"\n10.146.0.0/16 and 10.148.0.0/16 cannot allow a PTR record in Infoblox since they are managed by Microsoft DNS in EDC/LDC.";
       myresults=false;
     }
   }
   if (selectionValue != "A" && selectionValue != "TXT") {
     pingRez=ping("/pingsomething?address="+dnsRecordFQDN);
     pingJSON=JSON.parse(pingRez.responseText);
     if (pingJSON["results"]==0) {
       tosay=tosay+"\nFQDN is responding to ping! This utility can only add new records.";
       myresults=false;
     }
   }
//   if (!dnsRecordSCTASK.startsWith("sctask")) {
//       tosay=tosay+"\nThe SCTASK supplied must begin with 'SCTASK'.";
//       myresults=false;
//   }
   if (SNOWapp.startsWith("sctsk")||SNOWapp.startsWith("sctask")) {
       tosay=tosay+"\nIt looks like you are putting the SCTSK in the wrong field.";
       myresults=false;
   }
   if (SNOWapp.startsWith("ritm")) {
       tosay=tosay+"\nIt looks like you are putting an RITM as the Service Now application.";
       myresults=false;
   }

   if (! /^[a-zA-Z0-9\.\-\_]+$/.test(dnsRecordFQDN)) {
       tosay=tosay+"\nFQDNs can only contain alphanumeric characters, periods, or dashes.";
       myresults=false;
   }
   if (isEmptyOrSpaces(dnsValue) || isEmptyOrSpaces(dnsRecordFQDN) || isEmptyOrSpaces(selectionValue)) {
       tosay=tosay+"\nA required field is empty or whitespace.";
       myresults=false;
   }
   if (checkBadNames(dnsRecordFQDN)) {
       tosay=tosay+"\nProhibited entry being attempted for DNS FQDN.";
       myresults=false;
   }
   if (dnsRecordFQDN.includes(" ")) {
       tosay=tosay+"\nDNS FQDN cannot contain spaces.";
       myresults=false;
   }

   if (checkBadNames(dnsValue)) {
       tosay=tosay+"\nProhibited entry being attempted for DNS value.";
       myresults=false;
   }

   if (selectionValue=="CNAME" || selectionValue=="A" ||  selectionValue=="HOST") {
     if (dnsValue==dnsRecordFQDN) {
       tosay=tosay+"\nCannot use the same text for FQDN and value for this type of record.";
       myresults=false;
     }
   }
   if (selectionValue=="CNAME") {
     if (viewType=="External" || viewType =="Both") {

       if (/^(10)\.(.*)\.(.*)\.(.*)$/.test(socketJSON["results"]) || /^(172)\.(1[6-9]|2[0-9]|3[0-1])\.(.*)\.(.*)$/.test(socketJSON["results"]) || /^(192)\.(168)\.(.*)\.(.*)$/.test(socketJSON["results"])){
         tosay=tosay+"\nThe CNAME target is an internal IP address. You cannot add this to an external view.";
         myresults=false;
       }
     }
     if (dnsValue.includes(" ")) {
       tosay=tosay+"\nYou cannot have a space in a CNAME.";
       myresults=false;
     }
     if(dnsValue.match(regEx)) {
       tosay=tosay+"\nYou cannot link a CNAME to an IP address.";
       myresults=false;
     }
   }
   if (selectionValue=="A" || selectionValue=="HOST" || selectionValue=="PTR") {
    if (viewType=="External" || viewType =="Both") {
      if (/^(10)\.(.*)\.(.*)\.(.*)$/.test(dnsValue) || /^(172)\.(1[6-9]|2[0-9]|3[0-1])\.(.*)\.(.*)$/.test(dnsValue) || /^(192)\.(168)\.(.*)\.(.*)$/.test(dnsValue)){
       tosay=tosay+"\nYou cannot add an internal IP address to the external view.";
       myresults=false;
      }
    }
    
   if(!dnsValue.match(regEx))
     {
       tosay=tosay+"\nDNS record value must be an IPv4 address for the type of record you are adding.";
       myresults=false;
     document.getElementById("extravardnsRecordValue").focus();
     document.getElementById("extravardnsRecordValue").style.border = "1px solid red";
     }
    }
   if (!myresults) {
     alert(tosay);
     return false;
   }else{
     return true;
   }
   return false;
}    
function ptrShower() {
  var x = document.getElementById("extravardnsRecordType");
  myinput = x.value.toUpperCase();
  var dlw = document.getElementById("dnsCreatePTRdiv");
  if (myinput=="A") {
    dlw.style.display="block";
  }else{
    dlw.style.display="none";
  }
}

