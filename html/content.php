<?
include_once("config.php");
include_once("lib/xmlDbConnection.class.php");
include("common_functions.php");

//echo "<pre>";print_r($_REQUEST);echo "</pre>";


$id = $_REQUEST['id'];

$element = (isset($_REQUEST['element'])) ? $_REQUEST['element'] : null;
//$mode = ($element == 'did' || $element == 'c01') ? 'c-level-index' : 'summary';
//$mode = 'table';

$args = array('host' => $tamino_server,
	      'db' => $tamino_db,
	      'coll' => $tamino_coll,
	      'debug' => false);
$tamino = new xmlDbConnection($args);

switch ($element)
{
	case 'c01':
		$query = "
			for \$a in input()/ead/archdesc/dsc/c01 
			where \$a/@id='$id' 
			return <ead>{\$a}</ead>
		";		
		$mode = 'c-level-index';
	break;
	
	case 'c02':
		$query = "
			for \$a in input()/ead/archdesc/dsc/c01/c02 
			where \$a/@id='$id' 
			return <ead>{\$a}</ead>
		";		
		$mode = 'c-level-index';
	break;
		
	case 'did':
		$query = "
			for \$a in input()/ead/archdesc/did
			where \$a/@id='$id' 
			return <ead>{\$a}</ead>
		";		
		$mode = 'c-level-index';
	break;
	default:
		// query for all volumes 
		$query = "
			for \$a in input()/ead 
			where \$a/@id='$id' 
			return \$a
		";
		$mode = 'summary';
}

$xsl_file 	= "stylesheets/marblfa.xsl";
$xsl_params = array('mode' => $mode);

$rval = $tamino->xquery(trim($query));
$tamino->xslTransform($xsl_file, $xsl_params);

/*
echo "$id<br>";
echo "$mode<br>";
echo "$element<br>";
echo "$query<br>";
*/
?>

<? //include("htmlHead.html"); ?>

<? $tamino->printResult(); ?>
