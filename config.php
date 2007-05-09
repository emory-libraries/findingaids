<?php

/* Configuration settings for entire site */

$in_production = false;

// set level of php error reporting (warnings should be turned off in production)
if (! $in_production) {
  error_reporting(E_ALL ^ E_NOTICE);
}

/* tamino settings  */
$tamino_server = "vip.library.emory.edu";
$tamino_db = "EAD_TEST";
$tamino_coll = "MARBLFindingAids";


// settings for generating pdfs
$tmpdir = "/tmp/findingaids/";
$fop = "http://wilson:8080/fop/fop?fo=";

/* exist settings  */
if ($in_production) {
  $server = "bohr.library.emory.edu";		//production
} else {
  $server = "wilson.library.emory.edu";  	// test
}

$port = "8080";
$db = "FindingAids/emory";

$connectionArray = array('host'   => $server,
	      	    'port'   => $port,
		    'db'     => $db,
		    'dbtype' => "exist");


// shortcut to include common ead xquery functions
$eadxq = "import module namespace eadxq='http://www.library.emory.edu/xquery/eadxq' at
'xmldb:exist:///db/xquery-modules/ead.xqm'; ";

?>