
function getBrowserCSS () {

// determine browser & version
var name = navigator.appName;
var version = navigator.appVersion;
var os = navigator.platform;
var css = "iln.css";

if (name.match(/Internet Explorer/i)) {
  if (os.match(/mac/i)) {
    css = "iln-iemac.css";
  } else if (os.match(/win/i)) {
    css = "iln-iewin.css";
  }
}

//link to the appropriate stylesheet 
var css_link = '<link rel="stylesheet" type="text/css" href="http://cti.library.emory.edu/iln/';
var end_css = '"/>';

document.write(css_link+css+end_css);
}

//call the function
getBrowserCSS();
