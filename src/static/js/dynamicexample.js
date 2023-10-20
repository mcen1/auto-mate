function judgeUser() {
  var x = document.getElementById("extravarfavoritewebsite");
  myinput = x.value.toUpperCase();
  var dlw = document.getElementById("dontlikewebsites");
  var lw = document.getElementById("likewebsites");
  if (myinput=="") {
    dlw.style.display="none";
    lw.style.display="none";
  }else if (myinput=="NONE") {
    dlw.style.display="block";
    lw.style.display="none";
  }else{
    dlw.style.display="none";
    lw.style.display="block";
  }
}
