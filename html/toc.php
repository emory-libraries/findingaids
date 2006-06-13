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
/*$query = "
	for \$a in input()/ead 
	where \$a/@id='$id' 
	return \$a
";

*/

$query = "for \$a in input()/ead 
let \$ad := \$a/archdesc
where \$a/@id='$id' 
return <ead>
{\$a/@id}
<eadheader>
 <filedesc>
  <titlestmt>
   {\$a/eadheader/filedesc/titlestmt/titleproper}
  </titlestmt>
 </filedesc>
</eadheader>
<archdesc>
 <did>
 {\$ad/did/unittitle}
 </did>
 <dsc>
 {\$ad/dsc/head}
 {for \$c in \$ad/dsc/c01 
  return <c01> 
  {\$c/@id} {\$c/@level}
  <did>
   {\$c/did/unittitle}
   {\$c/did/physdesc}
  </did>
{-- adding c02 so c01 will display in xslt (kind of a hack) --}
  <c02/>
  </c01>}
 </dsc>
</archdesc>
</ead>";


$rval = $tamino->xquery(trim($query));
$tamino->xslTransform($xsl_file, $xsl_params);

//echo "<pre>"; print_r($tamino); echo "</pre>";
?>

<? //include("htmlHead.html"); ?>
<? $tamino->printResult(); ?>