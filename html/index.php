<?
error_reporting(E_ALL);
include_once("lib/xmlDbConnection.class.php");
include("common_functions.php");

$xmlDoc = new xmlDbConnection(null);

//include ("htmlHead.html");
//include ("heading.html");

echo "<link rel=\"stylesheet\" type=\"text/css\" href=\"css/marblfa.css\">\n";
echo "<body onload=\"MM_preloadImages('images/general-off.jpg')\">";

$xmlDoc->xmldb->xml = file_get_contents("home.xml");
$xmlDoc->xslTransform("stylesheets/site2html.xsl", null);

echo "</body>";
include ("home.html");
include ("footing.html");
?>