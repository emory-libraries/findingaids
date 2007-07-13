<?php
include("config.php");
include("common_functions.php");
include_once("lib/xml-utilities/xmlDbConnection.class.php");
include("lib/marblcrumb.class.php");

$connectionArray{"debug"} = false;

// search terms
$creator = $_REQUEST["creator"];
//$coll = "'/db/FindingAids/" . implode("', '/db/FindingAids/", $collections) . "'";
$coll = "'/db/FindingAids'";

// currently alphabetizing results;
// note: possibly privilege lastname matches?

// Susan requested that the creator list be limited to origination field, even though
// the creator search actually also searches controlled access fields as well

$query = "for \$b in distinct-values (
		for \$a in (collection($coll)$eadfilter//archdesc/did/origination)[. &= '$creator*']
		return normalize-space(\$a))
let \$c := count(collection($coll)${eadfilter}[.//archdesc/did/origination = \$b])
return <li>
<span class='count'>{\$c} collection{if (\$c !=1) then 's' else ()}</span>
<span class='value'>{\$b}</span>
</li>";    

// for some reason, count is not returning accurate results


/*
let \$c := count(collection($coll)$eadfilter[.//archdesc/did/origination &= '\$b' or 
	.//controlaccess/persname[@encodinganalog='700'][. &= '\$b'] or 
	.//controlaccess/corpname[@encodinganalog='710'][. &= '\$b'] or
	.//controlaccess/famname[@encodinganalog='700'][. &= '\$b']]
*/
$xmldb = new xmlDbConnection($connectionArray);

$xsl = "xslt/list.xsl";

// max to return ?
$xmldb->xquery($query, 1, 20);
$xmldb->xslTransform($xsl);

$xmldb->printResult();

?>
