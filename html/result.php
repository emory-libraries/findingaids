<?
require_once("common_functions.php");

$xml_file = "xml/findingAid.xml";
$xsl_file = "stylesheets/frameset.xsl";
$xsl_params = array('identifier' => key($_REQUEST));

$result = transform ($xml_file, $xsl_file, $xsl_params);
echo $result->saveHTML();

?>