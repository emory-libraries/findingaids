<?php
include("common_functions.php");
include_once("config.php");
include_once("lib/xml-utilities/xmlDbConnection.class.php");
include("lib/marblcrumb.class.php");


// letter to browse (A by default)
$letter = ($_REQUEST['l']) ? $_REQUEST['l'] : 'A';

$url = "browse.php";
if ($letter) {
  $url .= "?l=$letter";
  $mode = $letter == 'all' ? "All" : "($letter)";
}

$crumbs = new marblCrumb("Browse $mode", $url);
$crumbs->store();

$connectionArray{"debug"} = false;

$xmldb = new xmlDbConnection($connectionArray);

html_head("Browse Collections");
include("web/html/template-header.inc");
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
		for \$a in (//archdesc/did/origination/persname, //archdesc/did/origination/corpname,
			    //archdesc/did/origination/famname,
 			    //archdesc/did[not(exists(origination/*))]/unittitle)
		let \$l := substring(\$a,1,1)
		return \$l
	)
	order by \$b
	return <letter>{\$b}</letter>
";


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

$data_qry = "
	for \$a in /ead
	let \$sort-title := concat(\$a/archdesc/did/origination/persname,\$a/archdesc/did/origination/corpname,
			\$a/archdesc/did/origination/famname,\$a/archdesc/did[not(exists(origination/*))]/unittitle) 
	$letter_search
	order by \$sort-title
	return <record>
			{\$a/@id}
			<sort-title>{\$sort-title}</sort-title>
			<name>
				{\$a/archdesc/did/origination/persname}
				{\$a/archdesc/did/origination/corpname}
				{\$a/archdesc/did/origination/famname}
			</name>
			{\$a/archdesc/did/unittitle}
			{\$a/archdesc/did/physdesc}
			{\$a/archdesc/did/abstract}
		   </record>
";

$query = "<results><alpha_list>{".$browse_qry."}</alpha_list> <records>{".$data_qry."}</records></results>";

$mode = 'browse';

$xsl_file 	= "xslt/results.xsl";
$xsl_params = array('mode' => $mode,
		    'label_text' => "Browse Collections Alphabetically:",
		    'baseLink' => "browse.php",
		    'letter' => $letter);

$xmldb->xquery($query);
$xmldb->xslTransform($xsl_file, $xsl_params);

print '<div class="content">';
$xmldb->printResult();
print '</div>';

include("web/html/template-footer.inc");

?>
