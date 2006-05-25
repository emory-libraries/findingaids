<?
include_once("config.php");
include_once("lib/xmlDbConnection.class.php");
include("common_functions.php");

$id = $_REQUEST['id'];

$args = array('host' => $tamino_server,
	      'db' => $tamino_db,
	      'coll' => $tamino_coll,
	      'debug' => false);
$tamino = new xmlDbConnection($args);

$xsl_file 	= "stylesheets/marblfa.xsl";
$xsl_params = array('mode' => 'toc');

// query for all volumes 
$query = "
	for \$a in input()/ead 
	where \$a/@id='$id' 
	return \$a
";

$rval = $tamino->xquery(trim($query));
$tamino->xslTransform($xsl_file, $xsl_params);

//echo "<pre>"; print_r($tamino); echo "</pre>";
?>

<? //include("htmlHead.html"); ?>
<? $tamino->printResult(); ?>