<?php

/* Configuration settings for entire site */

// set level of php error reporting -- turn off warnings when in production
//error_reporting(E_ERROR | E_PARSE);


/* tamino settings  */
$tamino_server = "vip.library.emory.edu";
$tamino_db = "EAD_TEST";
$tamino_coll = "MARBLFindingAids";

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