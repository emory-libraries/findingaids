<?php
include("config.php");
include("common_functions.php");
include_once("lib/xmlDbConnection.class.php");
include("marblcrumb.class.php");

$connectionArray{"debug"} = false;

// search terms
$creator = $_REQUEST["creator"];
//$coll = "'/db/FindingAids/" . implode("', '/db/FindingAids/", $collections) . "'";
$coll = "'/db/FindingAids'";

$query = "for \$b in distinct-values (  
		for \$a in (collection($coll)$eadfilter//archdesc/did/origination,
			collection($coll)$eadfilter//controlaccess/persname[@encodinganalog='700'],
			collection($coll)$eadfilter//controlaccess/corpname[@encodinganalog='710'],
			collection($coll)$eadfilter//controlaccess/famname[@encodinganalog='700'])[. &= '$creator*']
		return normalize-space(\$a)) 
return <li>{\$b}</li>";    

// for some reason, count is not returning accurate results

/*
let \$c := count(collection($coll)$eadfilter[.//archdesc/did/origination &= '\$b' or 
	.//controlaccess/persname[@encodinganalog='700'][. &= '\$b'] or 
	.//controlaccess/corpname[@encodinganalog='710'][. &= '\$b'] or
	.//controlaccess/famname[@encodinganalog='700'][. &= '\$b']]
*/
$xmldb = new xmlDbConnection($connectionArray);

$xsl = "stylesheets/list.xsl";

// max to return ?
$xmldb->xquery($query, 1, 20);
$xmldb->xslTransform($xsl);

$xmldb->printResult();

?>
