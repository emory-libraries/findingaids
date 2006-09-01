<?php
include_once("common_functions.php");
include("marblcrumb.class.php");

$crumbs = new marblCrumb("Search", "rqst.php");
$crumbs->store();

html_head("Search - Finding Aids");
include("template-header.inc");

print $crumbs;

$kw = $_GET["keyword"];
$creator = $_GET["creator"];

include("searchform.php");

include("template-footer.inc");
?>