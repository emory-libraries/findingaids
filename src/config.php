<?php

/* Configuration settings for entire site */

$in_production = true;

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
$fop = "http://localhost:8080/fop/fop?fo=";

/* exist settings  */
if ($in_production) {
  $server = "bohr.library.emory.edu";
  $port = "7080";                              //production
} else {
  $server = "wilson.library.emory.edu";  	// test
  $port = "8080";
 }
$db = "FindingAids";

$connectionArray = array('host'   => $server,
	      	    'port'   => $port,
		    'db'     => $db,
		    'dbtype' => "exist");

// all the Finding Aid subcollections in eXist that contain Irish finding aids
$collections = array('emory', 'boston', 'wakeforest', 'wash-sl', 'ransom', 'delaware',
		     'southernillinois', 'pennstate', 'berg');

// xpath to limit finding aids to irish subjects for delmas 
$irishfilter = "eadheader/filedesc/titlestmt/titleproper/@type='Irish'";
$eadfilter = "/ead[$irishfilter]";


?>
