<?php

include("lib/breadcrumb.class.php");

class marblCrumb extends breadCrumb {

  function marblCrumb ($title = NULL, $url = NULL) {
    // do default initialization
    $this->breadCrumb();

    // if the breadcrumb cookie was empty, add top-level crumb
    if ($this->isEmpty()) {
      $this->add("Home", "index.php");
    }

    // add current page
    if (($title != NULL) && ($url != NULL)) $this->add($title, $url);
  }



    // check if a crumb is aquivalent to a current breadcrumb
  // if yes, return index within crumb array; if not, return 0
  function equivalent ($c) {
    for ($i = 0; $i < $this->count(); $i++) {
      $myc = $this->crumbs[$i];
      // exact duplicate - either page title or url is same
      if ($myc->url == $c->url || $myc->title == $c->title)
	return $i;
      
      // browse (any letter) is equivalent to search page in site hierarchy
      if ((strstr($myc->title, "Browse") || $myc->title == "Search" || strstr($myc->url,"doc.php")) &&
	   (strstr($c->title, "Browse") || $c->title == "Search" || strstr($c->url,"doc.php")))
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
  // for content page, id must match 
  // returns 1 if current page, 0 otherwise
  function currentPage ($link) {
    // content page serves out several levels of content (top-level, c01 - c03)
    if (strstr($link->url, "content.php")) {
      // compare the ids to check if it is the same page
      if (preg_match("/id=[^&]*/", $link->url, $matches)) {
	if (strstr($_SERVER['QUERY_STRING'], $matches[0]))
	  return true;
	else return false;
      }
    }
    // otherwise, do the default comparison (check link url without query terms against PHP_SELF)
    return parent::currentPage($link);
    
  }

  
}



?>
