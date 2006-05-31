<?php
include("common_functions.php");
include_once("config.php");
include_once("lib/xmlDbConnection.class.php");

$args = array('host' => $tamino_server,
	      'db' => $tamino_db,
	      'coll' => $tamino_coll,
	      'debug' => false);

$tamino = new xmlDbConnection($args);

switch ($browseBy)
{
	case 'unittitle':
	default:
		$search_path = "/archdesc/did/origination/persname";
		// query for all volumes 
}

$browse_qry = "
	for \$b in 
	distinct-values
	(
		for \$a in 
		(
			input()/ead/archdesc/did/origination/persname,
			input()/ead/archdesc/did/origination/corpname,
			input()/ead/archdesc/did/origination/famname
		)
		let \$l := substring(\$a,1,1)
		return \$l
	)
	return <letter>{\$b}</letter>
";



$letter = ($_REQUEST['l']) ? $_REQUEST['l'] : 'A';
if ($letter != 'all')
{
	$letter_search =  " where substring(\$a/archdesc/did/origination/persname,1,1) = '$letter' ";
	$letter_search .= " or substring(\$a/archdesc/did/origination/corpname,1,1) = '$letter' ";
	$letter_search .= " or substring(\$a/archdesc/did/origination/famname,1,1) = '$letter' ";
} else {
	$letter_search = "";
}

$data_qry = "
	for \$a in input()/ead
	$letter_search
	return <record>
			{\$a/@id}
			{\$a/archdesc/did/origination/persname}
			{\$a/archdesc/did/origination/corpname}
			{\$a/archdesc/did/origination/famname}
			{\$a/eadheader/filedesc/titlestmt/titleproper}
			{\$a/archdesc/did/physdesc}
			{\$a/archdesc/did/abstract}
		   </record>
   	sort by (unittitle)
";


$query = "<results><alpha_list>{".$browse_qry."}</alpha_list> <records>{".$data_qry."}</records></results>";
$mode = 'browse';

//echo $query;

$xsl_file 	= "stylesheets/results.xsl";
$xsl_params = array('mode' => $mode, 'label_text' => "Browse Collections Alphabetically:", 'baseLink' => "browse-coll");

$rval = $tamino->xquery(trim($query));
$tamino->xslTransform($xsl_file, $xsl_params);

html_head("Browse - Collections");
echo "<link rel=\"stylesheet\" type=\"text/css\" href=\"http://biliku.library.emory.edu/jbwhite/projects/marblfa-php/html/css/marblfa.css\">\n";
print '<div class="content">';
$tamino->printResult();
print '</div>';
?>
