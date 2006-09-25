<?
include_once("config.php");
include_once("lib/xmlDbConnection.class.php");

$id = $_GET["id"];

$query = "/ead[@id = '$id']";

$connectionArray{"debug"} = false;

$xmldb = new xmlDbConnection($connectionArray);

$xsl = "stylesheets/marblpdf.xsl";

$xmldb->xquery($query);
//$xmldb->xslTransform($xsl);
$params = array("mode" => "full");
$xmldb->xslBind("stylesheets/marblfa.xsl", $params);
$xmldb->xslBind("stylesheets/htmlpdf.xsl");
$xmldb->transform();
$xmldb->printResult();
?>