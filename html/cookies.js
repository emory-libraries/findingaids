/* This cookie class is a simplified version of the one in 
   _JavaScript:_The_Definitive_Guide_ by David Flanagan. 
*/

//Cookie constructor function
//args: document object, string name for the cookie to create
function Cookie (document, name) {
  this.$document = document;
  this.$name = name;
}

// store the values in the cookie
function _Cookie_store () {
  //  this.$document.cookie = this.$name + '=' + val;
  var cookieval = "";
  
  // add all properties that do not start with $ and are not functions
  // store properties as name:value&name2:value2
  for (var prop in this) {
    if ((prop.charAt(0) == '$') || (typeof this[prop] == 'function')) continue; 
    if (cookieval != "") cookieval += '&';
    cookieval += prop + ':' + escape (this[prop]);
  }

  var cookie = this.$name + '=' + cookieval;
  // store the cookie
  this.$document.cookie = cookie;

}

//returns a stored cookie value
function _Cookie_load () {
  var allcookies = this.$document.cookie;
  if (allcookies == "") return false;

  var start = allcookies.indexOf(this.$name + '=');
  if (start == -1) return false;  //cookie not defined
  //determine beginning & ending of string
  start += this.$name.length + 1;  //start after cookie name & = sign
  var end = allcookies.indexOf(';', start);
  if (end == -1) end = allcookies.length;
  var cookieval = allcookies.substring(start,end);

  var a = cookieval.split('&');		// split cookie into array of name:value pairs
  for (var i = 0; i < a.length; i++) {
    a[i] = a[i].split(':');		// split each pair into an array
  }
 
  // set name & unescaped value
  for (var i = 0; i < a.length; i++) {
    this[a[i][0]] = unescape(a[i][1]);
  }
   
  return true;
}

//bind the functions into object methods
new Cookie();
Cookie.prototype.store = _Cookie_store;
Cookie.prototype.load = _Cookie_load;



