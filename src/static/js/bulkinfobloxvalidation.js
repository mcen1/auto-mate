function socketLookup(myURL){
  return $.ajax({
    url: myURL,
    async: false
  });
}
function ping(myURL){
  return $.ajax({
    url: myURL,
    async: false
  });
}


function checkBadNames(mything) {
  try {
   if (mything.includes("127.0.0.1") || mything.includes("localhost")) {
      return true;
    }
  }
  catch (err) {
    console.log(err);
  }
  return false;
}
function isEmptyOrSpaces(str){
  try {
    return str === null || str.match(/^ *$/) !== null;
  }
  catch (err) {
    console.log(err);
  }
  return false;
}
function validateForm() {
   var maxrows=50;
   var SNOWapp = document.getElementsByName('extravardnsRecordApplication')[0].value.toLowerCase();
   var dnsRecordSCTASK = document.getElementsByName('extravardnsRecordSCTASK')[0].value.toLowerCase();
   var myresults=true;
   var tosay="";
   var regEx = /^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
   var lines = document.getElementById("extravardnsBulk").value.split('\n');
   // # fqdn,value,type,view
   if (lines.length>maxrows) {
     tosay=tosay+`\nMaximum number of lines exceeded. Max is ${maxrows}`;
   }
   for(var i = 0;i < lines.length;i++){
     myline=lines[i].toLowerCase().split(',');
     mylinetotal=lines[i].trim();
     if (myline[2] != "a" && myline[2] != "txt" && myline[2] != "aptr") {
       pingRez=ping("/pingsomething?address="+myline[0]);
       pingJSON=JSON.parse(pingRez.responseText);
       if (pingJSON["results"]==0) {
         tosay=tosay+`\nError on line ${i+1}: FQDN is responding to ping! This utility can only add new records.`;
         myresults=false;
       }
     }

     if (mylinetotal=="") {
       tosay=tosay+`\nError on line ${i+1}: line is empty. Please remove it.`;
       myresults=false;
     }
     if (myline.length!=4 && mylinetotal!="") {
       tosay=tosay+`\nError on line ${i+1}: Insufficient amount of fields provided. Need 4, found ${myline.length}.`;
       myresults=false;
     }
     if (myline[0].includes("dir.health") && (myline[3]=="internal" || myline[3] =="both")) {
       tosay=tosay+`\nError on line ${i+1}: dir.health entries for the Internal view are not managed by Infoblox at this time.`;
       myresults=false;
     }
     if (myline[2] == "ptr" || myline[2]=="aptr") {
       if (myline[1].startsWith("10.146.")||myline[1].startsWith("10.148.")) {
         tosay=tosay+`\nError on line ${i+1}: 10.146.0.0/16 and 10.148.0.0/16 cannot allow a PTR record in Infoblox since they are managed by Microsoft DNS in EDC/LDC.`;
         myresults=false;
       }
     }
     if (! /^[a-zA-Z0-9\.\-\_]+$/.test(myline[0]) && mylinetotal!="") {
       tosay=tosay+`\nError on line ${i+1}: DNS record names can only contain alphanumeric characters, periods, or dashes.`;
       myresults=false;
     }
     if ((isEmptyOrSpaces(myline[0]) || isEmptyOrSpaces(myline[1]) || isEmptyOrSpaces(myline[2]) || isEmptyOrSpaces(myline[3])) && mylinetotal!="") {
       tosay=tosay+`\nError on line ${i+1}: A required field is empty or whitespace.`;
       myresults=false;
     }
     if (checkBadNames(myline[0])) {
       tosay=tosay+`\nError on line ${i+1}: Prohibited entry being attempted for DNS record name.`;
       myresults=false;
     }
     if (myline[0].includes(" ")) {
       tosay=tosay+`\nError on line ${i+1}: DNS record name cannot contain spaces.`;
       myresults=false;
     }

     if (checkBadNames(myline[1])) {
       tosay=tosay+`\nError on line ${i+1}: Prohibited entry being attempted for DNS value.`;
       myresults=false;
     }
   if (myline[2]!="cname" && myline[2]!="a" && myline[2]!="aptr" && myline[2]!="txt" && myline[2]!="ptr") {
     tosay=tosay+`\nError on line ${i+1}: Unsupported record type.`;
     myresults=false;
   }
   if (myline[3]!="internal" && myline[3]!="external" && myline[3]!="both") {
      tosay=tosay+`\nError on line ${i+1}: Unsupported view.`;
      myresults=false;
   }
   if (myline[2]=="cname" || myline[2]=="a" ||  myline[2]=="aptr") {
     if (myline[1]==myline[0]) {
       tosay=tosay+`\nError on line ${i+1}: Cannot use the same text for name and value for this type of record.`;
       myresults=false;
     }
   }
   if (myline[2]=="cname") {
     if (myline[3]=="external" || myline[3] =="both") {
       var socketRez=socketLookup("/socketlookup?address="+myline[1]);
       var socketJSON=JSON.parse(socketRez.responseText)
       if (/^(10)\.(.*)\.(.*)\.(.*)$/.test(socketJSON["results"]) || /^(172)\.(1[6-9]|2[0-9]|3[0-1])\.(.*)\.(.*)$/.test(socketJSON["results"]) || /^(192)\.(168)\.(.*)\.(.*)$/.test(socketJSON["results"])){
         tosay=tosay+`\nError on line ${i+1}: The CNAME target is an internal IP address. You cannot add this to an external view.`;
         myresults=false;
       }
     }

     if (myline[1].includes(" ")) {
       tosay=tosay+`\nError on line ${i+1}: You cannot have a space in a CNAME.`;
       myresults=false;
     }
     if(myline[1].match(regEx)) {
       tosay=tosay+`\nError on line ${i+1}: You cannot link a CNAME to an IP address.`;
       myresults=false;
     }
   }
   if (myline[2]=="a" || myline[2]=="aptr" || myline[2]=="ptr") {
    if (myline[3]=="external" || myline[3] =="both") {
      if (/^(10)\.(.*)\.(.*)\.(.*)$/.test(myline[1]) || /^(172)\.(1[6-9]|2[0-9]|3[0-1])\.(.*)\.(.*)$/.test(myline[1]) || /^(192)\.(168)\.(.*)\.(.*)$/.test(myline[1])){
       tosay=tosay+`\nError on line ${i+1}: You cannot add an internal IP address to the external view.`;
       myresults=false;
      }
    }
   if(!myline[1].match(regEx))
     {
       tosay=tosay+`\nError on line ${i+1}: DNS record value must be an IPv4 address for the type of record you are adding.`;
       myresults=false;
     }
    }
   }
   if (SNOWapp.startsWith("sctsk")||SNOWapp.startsWith("sctask")) {
       tosay=tosay+`\nIt looks like you are putting the SCTSK in the wrong field.`;
       myresults=false;
   }
   if (SNOWapp.startsWith("ritm")) {
       tosay=tosay+`\nIt looks like you are putting an RITM as the Service Now application.`;
       myresults=false;
   }

   if (!myresults) {
     alert(tosay);
     return false;
   }else{
     return true;
   }
   return false;
}    

