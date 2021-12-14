function delete_from_watched(title) {
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
      var id_unwatch_name = title+"_unwatch"
      document.getElementById(id_unwatch_name).disabled = true
      document.getElementById("info").style.visibility = "visible"
      document.getElementById("info_text").innerText = "Successfully deleted from watched " + title
      console.log(title)
    }
  };
  xhttp.open("POST", "/unrate", true);
  xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  xhttp.send("title="+title);
}

function delete_from_want_to_watch(title, id_unwant_name, id_want_name) {
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
      document.getElementById(id_unwant_name).disabled = true
      document.getElementById(id_want_name).disabled = false
      document.getElementById("info").style.visibility = "visible"
      document.getElementById("info_text").innerText = "Successfully deleted from watchlist " + title
      console.log(title)
    }
  };
  xhttp.open("POST", "/unwant", true);
  xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  xhttp.send("title="+title);
}

function add_to_want_to_watch(title, id_unwant_name, id_want_name) {
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
      document.getElementById(id_unwant_name).disabled = false
      document.getElementById(id_want_name).disabled = true
      document.getElementById("info").style.visibility = "visible"
      document.getElementById("info_text").innerText = "Successfully added to watchlist" + title
      console.log(title)
    }
  };
  xhttp.open("POST", "/want", true);
  xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  xhttp.send("title="+title);
}

function add_to_watched(title){
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
      console.log('aa')
      var id_unwatch_name = title+"_unwatch"
      var id_rate_name = title + "_rate"
      var id_rated_name = title + "_rated"
      rate = document.getElementById(id_rate_name).value
      document.getElementById("info").style.visibility = "visible"
      document.getElementById("info_text").innerText = "Successfully rated" + title
      document.getElementById(id_unwatch_name).disabled = false
      document.getElementById(id_rated_name).innerText = rate
      document.getElementById(id_rated_name).style.fontWeight = 'bold'
      console.log(title)
    }
  };
  var id_rate_name = title + "_rate"
  rate = document.getElementById(id_rate_name).value
  xhttp.open("POST", "/rate", true);
  xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  xhttp.send("title="+title+"&rate="+rate);

}