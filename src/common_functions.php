<?php

// php functions & variables used by more than one ILN php page
include("config.php");

$baseURL  = "http://marbl.library.emory.edu";


/* 12.10.2004 - Added robots meta line to header, partially as a test
   to see if it would help google to index the actual articles.
*/

function html_head ($mode, $contentlist = false) {
  global $baseURL;
  // FIXME: this is the doctype from the template, but template html is NOT valid XHTML
  //  print "<!DOCTYPE html PUBLIC '-//W3C//DTD XHTML 1.0 Transitional//EN'
  //    'http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd'>
print '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head profile="http://gmpg.org/xfn/11">
	<title>Emory MARBL | Finding Aids | ' . $mode . '</title>
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
	<meta http-equiv="Content-Language" content="en-us" />
	<meta name="robots" content="all" />
	<meta http-equiv="imagetoolbar" content="false" />
	<meta name="MSSmartTagsPreventParsing" content="true" />
	
	<style type="text/css" media="all">
		@import url( "http://marbl.library.emory.edu/css/mq_standardstyles_0.1.css" );
		@import url( "http://marbl.library.emory.edu/css/marbl_fa.css" );    
	</style>
	
	<link rel="stylesheet" type="text/css" media="print" href="http://marbl.library.emory.edu/css/print.css" />

	<script language="Javascript" type="text/javascript">
	  function pdfnotify (url) {
  	     window.open("web/html/pdfstatus.html", "pdfstatus", "width=300,height=125,toolbar=no,status=no,location=no,menubar=no,scrollbars=no,screenX=300,screenY=300,left=300,top=300,resizable=no");
 	  }
	</script>
</head>';
}



// param arg is optional - defaults to null
function transform ($xml_file, $xsl_file, $xsl_params = NULL) {
	$xsl = new DomDocument();
	$xsl->load($xsl_file);
	
	$xml = new DOMDocument();
	$xml->load($xml_file);
	
	/* create processor & import stylesheet */
	$proc = new XsltProcessor();
	$proc->importStylesheet($xsl);
	if ($xsl_params) {
		foreach ($xsl_params as $name => $val) {
			$proc->setParameter(null, $name, $val);
		}
	}
	/* transform the xml document and store the result */
	$xsl_result = $proc->transformToDoc($xml);
	
	return $xsl_result;
}

//Function that takes multiple terms separated by white spaces and puts them into an array
function processterms ($str) {
// clean up input so explode will work properly
    $str = preg_replace("/\s+/", " ", $str);  // multiple white spaces become one space
    $str = preg_replace("/\s$/", "", $str);	// ending white space is removed
    $str = preg_replace("/^\s/", "", $str);  //beginning space is removed
    $terms = explode(" ", $str);    // multiple search terms, divided by spaces
    return $terms;
}




?>
