<?
include_once("config.php");
include_once("common_functions.php");

// not including marblcrumb here because this is the start of the trail...

html_head("Irish Literary Collections");
include("template-header.inc");

print "<div id='index'>\n";

// FIXME: edit alt/title text for these images (get descriptions from Susan)
$img[0] = array("images/home-1.jpg", "sample book covers of Irish holdings");
$img[1] = array("images/home-2.jpg", "sample manuscripts from Irish holdings");
$img[2] = array("images/home-3.jpg", "sample broadsides and theater programs from Irish holdings");

$n = rand(0, (count($img) - 1));
print "<img id='frontpage' src='" . $img[$n][0] . "' alt='" . $img[$n][1] . "' title='" . $img[$n][1] . "'/>";


print "<p>The Irish Literary Collections Portal provides access to the finding aids of
over 100 of North America's Irish literary manuscript collections.</p>\n";

print "</div>\n";

include("template-footer.inc");

?>
