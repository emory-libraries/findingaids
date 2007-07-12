<?php
include("common_functions.php");
include_once("config.php");
include_once("lib/xml-utilities/xmlDbConnection.class.php");
include("marblcrumb.class.php");


// letter to browse (all by default)
$letter = ($_REQUEST['l']) ? $_REQUEST['l'] : 'all';

$repo = ($_REQUEST['repository']) ? $_REQUEST['repository'] : 'all';

// by default, search all 
$coll = "/db/FindingAids";
if (($repo != "all") && (in_array($repo, $collections))) {
      $coll .= "/$repo";
    }
// put quotes around collection for use in xquery collection statement
$coll = "'$coll'";


$url = "browse.php";
$urlopts = array();
if ($letter) {
  array_push($urlopts, "l=$letter");
  $mode = $letter == 'all' ? "All" : "($letter)";
}
if ($repo != 'all')
  array_push($urlopts, "repository=$repo");

$url .= "?" . implode('&', $urlopts);


$crumbs = new marblCrumb("Browse $mode", $url);
$crumbs->store();

$connectionArray{"debug"} = false;

$xmldb = new xmlDbConnection($connectionArray);

html_head("Browse Collections");
include("template-header.inc");
// custom style for browse page only
print "<style> div.content { margin-right:1in; } </style>";
print $crumbs;

// unused (allow browsing by something besides unittitle ?)
switch ($browseBy) {
 case 'unittitle':
 default:
   $search_path = "/archdesc/did/origination/persname";
   // query for all volumes 
}




// note: in all cases, unit title is used as a fall-back *only* if no origination name exists
// xquery to get the first letters of all titles (used to generate alpha list)
$browse_qry = "
	for \$b in 
	distinct-values (
		for \$a in (collection($coll)$eadfilter//archdesc/did/origination/persname,
			    collection($coll)$eadfilter//archdesc/did/origination/corpname,
			    collection($coll)$eadfilter//archdesc/did/origination/famname,
			    collection($coll)$eadfilter//archdesc/did/origination/title,
 			    collection($coll)$eadfilter//archdesc/did[not(exists(origination/*))]/unittitle)
	let \$l := substring(\$a,1,1)";
//if ($repo != 'all') $browse_qry .= " where root(\$a)/ead/eadheader/eadid/@mainagencycode = '$repo' ";
$browse_qry .= "
		return \$l
	)
	order by \$b
	return <letter>{\$b}</letter>
";


/*$repository_qry = 'for $r in distinct-values(/ead/eadheader/eadid/@mainagencycode)
let $rep := (/ead[eadheader/eadid/@mainagencycode = $r]/archdesc/did/repository)[1] 
order by $rep 
return <repository agencycode="{$r}">{$rep/@*} {$rep/node()}</repository>';*/


/* organize by exist collection structure */
$repository_qry = 'for $r in ("' . implode('", "', $collections) . '")  
let $coll := concat("/db/FindingAids/", $r) 
let $code := distinct-values(collection($coll)//ead/eadheader/eadid/@mainagencycode) 
let $rep := (collection($coll)/ead/archdesc/did/repository)[1] 
order by $rep  
return <repository collection="{$r}" agencycode="{$code}">
	{$rep/@*}
	{$rep/node()}
</repository>';



// if a letter is specified, match the first letter of the origination name or title field 
if ($letter != 'all') {
  $letter_search = " where starts-with(\$sort-title, '$letter') ";
  //	$letter_search =  " where starts-with(\$a//origination/persname,'$letter') ";
  //	$letter_search .= " or starts-with(\$a//origination/corpname,'$letter') ";
  //	$letter_search .= " or starts-with(\$a//origination/famname,'$letter') ";
  //       	$letter_search .= " or starts-with(\$a//archdesc/did[not(exists(origination/*))]/unittitle,'$letter') ";
} else {
  // otherwise, no filter is needed (return all collections)
	$letter_search = "";
}

/*if ($repo != 'all') {
  $repository_filter = "[eadheader/eadid/@mainagencycode = '$repo']";
} else {
  $repository_filter = "";
  }*/

//	for \$a in /ead[archdesc/$irishfilter]$repository_filter

// note: using unittitle as secondary sorting for finding aids with repeated originations
$data_qry = "
	for \$a in collection($coll)/ead[$irishfilter]
	let \$sort-title := concat(\$a/archdesc/did/origination/persname,\$a/archdesc/did/origination/corpname,
			\$a/archdesc/did/origination/famname,\$a/archdesc/did/origination/title,
			\$a/archdesc/did/unittitle) 
	$letter_search
	order by \$sort-title
	return <record>
			{\$a/@id}
			<sort-title>{\$sort-title}</sort-title>
			<name>
				{\$a/archdesc/did/origination/persname}
				{\$a/archdesc/did/origination/corpname}
				{\$a/archdesc/did/origination/famname}
				<origination>{\$a/archdesc/did/origination/title}</origination>
			</name>
			{\$a/archdesc/did/unittitle}
			{\$a/archdesc/did/physdesc}
			{\$a/archdesc/did/abstract}
			{\$a/archdesc/did/repository}
		   </record>
";

$query = "<results><alpha_list>{".$browse_qry."}</alpha_list>
	  <source>{" . $repository_qry . "}</source>
 	  <records>{".$data_qry."}</records></results>";

$mode = 'browse';


$xsl_file 	= "stylesheets/results.xsl";
$xsl_params = array('mode' => $mode,
		    'label_text' => "Browse Collections Alphabetically:",
		    'baseLink' => "browse.php",
		    "letter" => $letter,
		    "repository" => $repo);

$xmldb->xquery($query);
$xmldb->xslTransform($xsl_file, $xsl_params);

print '<div class="content">';
$xmldb->printResult();
print '</div>';

include("template-footer.inc");

?>
