<?php

  // note: this page just lays out the search form; the actual work of searching is done in search.php

include_once("common_functions.php");
include("marblcrumb.class.php");

$crumbs = new marblCrumb("Search", "rqst.php");
$crumbs->store();

html_head("Search - Finding Aids");
include("template-header.inc");

print $crumbs;

// the form itself is separate, so it can be included when no matches
// are found (allows users to edit their search terms)
include("searchform.php");

include("template-footer.inc");
?>