<?php
include("common_functions.php");
include_once("config.php");
include_once("lib/xmlDbConnection.class.php");

$connectionArray{"debug"} = false;

$tamino = new xmlDbConnection($connectionArray);

switch ($browseBy)
{
	case 'unittitle':
	default:
		$search_path = "/archdesc/did/origination/persname";
		// query for all volumes 
}

// note: in all cases, unit title is used as a fall-back *only* if no origination name exists

$browse_qry = "
	for \$b in 
	distinct-values
	(
		for \$a in (//archdesc/did/origination/persname, //archdesc/did/origination/corpname,
			    //archdesc/did/origination/famname, //archdesc/did[not(exists(origination/*))]/unittitle)
		let \$l := substring(\$a,1,1)
		return \$l
	)
	order by \$b
	return <letter>{\$b}</letter>
";



$letter = ($_REQUEST['l']) ? $_REQUEST['l'] : 'A';
if ($letter != 'all')
{
	$letter_search =  " where starts-with(\$a//origination/persname,'$letter') ";
	$letter_search .= " or starts-with(\$a//origination/corpname,'$letter') ";
	$letter_search .= " or starts-with(\$a//origination/famname,'$letter') ";
       	$letter_search .= " or starts-with(\$a//archdesc/did[not(exists(origination/*))]/unittitle,'$letter') ";
} else {
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

/*
{ for \$i in (\" \", \"'\", \"A \", \"An \", \"The \", \"\", \"The Register of the \", \"A Register of \", \"The Register of \", \"Register of \", \"Register \") where starts-with(\$a/archdesc/did/unittitle, \$i)
			 	return substring-after(\$a/archdesc/did/unittitle, \$i) }
*/

$query = "<results><alpha_list>{".$browse_qry."}</alpha_list> <records>{".$data_qry."}</records></results>";

$mode = 'browse';

$xsl_file 	= "stylesheets/results.xsl";
$xsl_params = array('mode' => $mode, 'label_text' => "Browse Collections Alphabetically:", 'baseLink' => "browse-coll");

$rval = $tamino->xquery(trim($query));
$tamino->xslTransform($xsl_file, $xsl_params);

echo "<link rel=\"stylesheet\" type=\"text/css\" href=\"http://biliku.library.emory.edu/rebecca/marblfa-php/html/css/marblfa.css\">\n";
print '<div class="content">';
$tamino->printResult();
print '</div>';
?>
