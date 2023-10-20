function validateForm() {
   var formUsername = document.getElementsByName('extravarns_username')[0].value.toLowerCase();
   var myresults=true;
   var tosay="";
   if (formUsername.endsWith("_tr1")) {
     tosay=tosay+"\nPlease supply a non-tier 1 username.";
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
