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
// test
$server = "wilson.library.emory.edu";
//production
//$server = "bohr.library.emory.edu";
$port = "8080";
//$db = "FindingAids";
$db = "FindingAids/emory";

$connectionArray = array('host'   => $server,
	      	    'port'   => $port,
		    'db'     => $db,
		    'dbtype' => "exist");

?>