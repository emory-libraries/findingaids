<?php
include("common_functions.php");
include_once("config.php");
include_once("lib/xmlDbConnection.class.php");
include("marblcrumb.class.php");

// name of document to retrieve
$docid = $_REQUEST['id'];



$connectionArray{"debug"} = false;

$xmldb = new xmlDbConnection($connectionArray);

$query = "document('/db/$db/delmas-docs/$docid.xml')/div";

$xmldb->xquery($query);
$doctitle = $xmldb->findNode("h1");

$url = "doc.php?id=$docid";
$crumbs = new marblCrumb($doctitle, $url);
$crumbs->store();

html_head($doctitle);
include("template-header.inc");
print $crumbs;

print '<div class="content">';
print $xmldb->getXML();
print '</div>';

include("template-footer.inc");


