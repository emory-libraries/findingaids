<?php

include("lib/breadcrumb.class.php");

class marblCrumb extends breadCrumb {

  function marblCrumb ($title = NULL, $url = NULL) {
    // do default initialization
    $this->breadCrumb();

    // if the breadcrumb cookie was empty, add top-level crumb
    if (count($this->crumbs) == 0) {
      // FIXME: can we use a relative url here?  try copying index.html over...
      $this->add("MARBL Finding Aids", "http://marbl.library.emory.edu/FindingAids/");
    }

    // add current page
    if (($title != NULL) && ($url != NULL)) $this->add($title, $url);
  }


  // need to override isDup - browse = search; content pages?


    // check if a crumb is an exact duplicate (title and url both) of a current breadcrumb
  // if yes, return index within crumb array; if not, return 0
  function isDup ($c) {
    for ($i = 0; $i < count($this->crumbs); $i++) {
      $myc = $this->crumbs[$i];
      // exact duplicate - either page title or url is same
      if ($myc->url == $c->url || $myc->title == $c->title)
	return $i;
      
      // browse (any letter) is equivalent to search page in site hierarchy
      if ((strstr($myc->title, "Browse") || $myc->title == "Search") &&
	  (strstr($c->title, "Browse") || $c->title == "Search"))
	return $i;

      // content documents - top level & subseries of finding aid
      // note: using strstr because strpos returns 0 since content.php is at the beginning of url
      if (strstr($myc->url, "content.php") && strstr($c->url, "content.php")) {

	// top level of finding aid - either no element or ead specified
	if ( (!(strstr($myc->url, "el=")) || strpos($myc->url, "el=ead"))
	     && (!(strstr($c->url, "el=")) || strpos($c->url, "el=ead"))) 
	  return $i;

	// documents at the same c0n level should be considered equivalent
	if (preg_match("/el=c0([123])/", $myc->url, $mymatch)) {
	  preg_match("/el=c0([123])/", $c->url, $newmatch);
	  // c-level is equivalent to or lower (higher in doc) than current
	  if ($newmatch[0] <= $mymatch[0]) 
	    return $i;
	}
      }	// end content doc
    }
    
    // no equivalencies found; new crumb is not a dup
    return 0;
  }


  
  // check if a specified link is equivalent to the current page
  // simple check: compare current PHP_SELF to specified url, without query options
  // returns 1 if current page, 0 otherwise
  function currentPage ($link) {
    if (strstr($link->url, "content.php")) {
      if (preg_match("/id=[^&]*/", $link->url, $matches)) {
	if (strstr($_SERVER['QUERY_STRING'], $matches[0]))
	  return 1;
	else return 0;
      }
    }
    if (strpos($link->url, '?')) {
      $baseurl = substr($link->url, 0, strpos($link->url,'?'));
    } else {
      $baseurl = $link->url;
    }
    return strpos($_SERVER['PHP_SELF'],$baseurl);
  }

  // need to override currentPage = content page needs to check el/id
  
}



?>