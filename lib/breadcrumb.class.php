<?php 
/**
 * Store user history in a cookie and display as a breadcrumb
 *
 * This class is really kind of a history-crumb (or cookie crumb); it
 * stores pages & links in a cookie in the following format:
 * title:=:link|title2:=:link2 ... etc
 * (Note: this class does not using serialize because, according to
 * php.net, serialize is not recommended / not secure for use with
 * cookies)
 * This class is designed to be extended as needed for specific sites;
 * specifically, the logic for determining duplicates [equivalent()]
 * and for determining if a url is the current page [currentPage()]
 * (see marblfa-php/marblcrum for an example of a customized version)
 *
 * @author Rebecca Sutton Koeser (rebecca.s.koeser@emory.edu), August 2006
 */
  
class breadCrumb {

  /**
   * @var array array of links (page title + url)
   */
  var $crumbs;
  /**
   * @var string name to use for cookie where breadcrumbs are stored
   */
  var $cookie;
  /**file:////usr/local/Zend/ZendStudioClient-5.1.0/docs/PHPmanual/
   * @var string $separator delimiter for output display (default: > )
   */
  var $separator;
  
  /**
   * Initialize breadcrumb object and get any breadcrumbs previously stored in cookie
   */
  function breadCrumb() {
    $this->crumbs = array();
    $this->cookie = "history";

    // default separator string for output 
    $this->separator = " > ";

    // get any pages stored in the breadcrumb cookie
    if (isset($_COOKIE[$this->cookie])) {
      // setcookie seems to implicitly add slashes, so remove them here
      $cookiecrumb = stripslashes($_COOKIE[$this->cookie]);
      // if there is more than one breadcrumb saved, explode into an array
      foreach (explode('|', $cookiecrumb) as $c) {
	array_push($this->crumbs, new link($c));
      }
    }
  }

  /**
   * Add a new link to the breadcrumb trail
   *
   * Add the specified link (title + url) to breadcrumbs; if the new
   * link is equivalent to an existing link already in the
   * breadcrumbs, the equivalent link & all links after it will be
   * removed and replaced with the new link.  Otherwise, the new link
   * is added to the end of the breadcrumb.
   *
   * @param string $title Title
   * @param string $url URL
   * 
   */
  function add($title, $url) {
    $newcrumb = new link($title, $url);
    // don't add an equivalent/duplicate page (e.g., on refresh)
    $dup = $this->equivalent($newcrumb);
    // if there is an equivalent crumb, get rid of it and all following links
    //   (dupes may be equivalent instead of exactly equal,
    //    so the new equivalent link should take precedence)
    if ($dup) {
      $count = count($this->crumbs);
      for ($i = $dup; $i < $count; $i++) {
	unset($this->crumbs[$i]);
      }
    }
    // add new or re-add "dup" / equivalent
    array_push($this->crumbs, $newcrumb);
  }


  /**
   * Check if any existing breadcrumbs are equivalent to the specified link
   *
   * Checks if a link is equivalent to an existing breadcrumb; in this
   * case, it only checks for exact duplication of both title & url,
   * but is intended to be extended to allow for more complicated
   * kinds of equivalences within a specific site.
   *
   * @param link $c link to compare
   * @return int index of equivalent crumb, 0 if not equivalent to any
   */
  function equivalent ($c) {
    for ($i = 0; $i < $this->count(); $i++) {
      if ($this->crumbs[$i]->title == $c->title &&
	  $this->crumbs[$i]->url == $c->url) {
	return $i;
      }
    }
    return 0;
  }

  /**
   * Write the breadcrumb values out to a cookie
   *
   * Convert the breadcrumb titles & urls into a delimited string and
   * write to a cookie.  Values are stored in the following format:
   * title:=:link|title2:=:link2 ... etc.
   */
  function store() {
    $cookiecrumb = array();
    foreach ($this->crumbs as $c) {
      array_push($cookiecrumb, $c->toCookie());
    }
    $cookiestr = implode('|', $cookiecrumb);
    setcookie($this->cookie, $cookiestr);
  }

  /**
   * Convert breadcrumbs to a string for printed
   *
   * Converts breadcrumbs into html for display.  Uses currentPage()
   * function to detect if a link is the current page, in which case
   * it displays only the title (not an active link).  Note that for
   * styling purposes, the breadcrumbs are output in a div with class
   * breadCrumbs.
   *
   * Example of the ease of printing breadcrumbs:
   * <code>
   *  $crumb = new breadCrumb();
   *  print $crumb;
   * </code>
   */
  function __toString() {
    $pagecrumbs = array();
    foreach ($this->crumbs as $c) {	
      // don't link to the current page
      if ($this->currentPage($c)) {
	array_push($pagecrumbs, $c->title);
      } else {
	array_push($pagecrumbs, $c->toHtml());
      }
    }
    $string = "<div class='breadCrumbs'>" . implode($this->separator, $pagecrumbs) . "</div>";
    return $string;
  }

  /**
   * Check if a specified link is equivalent to the current page
   *
   * This function is used for displaying breadcrumbs, to keep the
   * current page from being printed as an active link.  In this case,
   * only a simple check is done: it compares current PHP_SELF to the
   * specified url (ignoring query options).  This function is
   * intended to be extended for more complicated checks (e.g., if
   * query parameters must be taken into account).
   *
   * @param link
   * @return boolean true if link is current page, false otherwise
   * 
   */
  function currentPage ($link) {
    $p = strpos($link->url, '?');
    if ($p) {
      // get the url without query options
      $baseurl = substr($link->url, 0, $p);
    } else {
      $baseurl = $link->url;
    }
    // check if PHP_SELF matches current url
    if (strpos($_SERVER['PHP_SELF'],$baseurl))
      return true;
    else
      return false;
  }

  /**
   * Check if crumb list is empty
   *
   * @return boolean
   */
  function isEmpty () {
    if ($this->count())
      return false;
    else return true;
  }

  /**
   * Returns the number of entries in the breadcrumb list
   * 
   * @return int count
   */
  function count () {
    return count($this->crumbs);
  }

}

/**
 * Minimal link class
 *
 */
class link {
  var $title;
  var $url;

  /**
   * Initialize link object
   *
   * Accepts either title & link or cookie-style combo (title:=:link)
   *
   * @param string title or title:=:link
   * @param string url (optional)
   */
  function link($t, $u = NULL) {
    if ($u != NULL) {
      $this->title = $t;
      $this->url = $u;
    } else {
      $t = explode(':=:', $t);
      $this->title = $t[0];
      $this->url = $t[1];
    }
  }

  /**
   * Convert link to html-formatted string for display
   * 
   * @return string html link
   */
  function toHtml() {
    return "<a href='$this->url'>" . stripslashes($this->title) . "</a>";
  }

  /**
   * Convert link to delimited string for storing in cookie
   *
   * @return string delimited link (title:=:url)
   */
  function toCookie() {
    return "$this->title:=:$this->url";
  }
  
}