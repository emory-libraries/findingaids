<?php
include("config.php");
include("common_functions.php");
include_once("lib/xmlDbConnection.class.php");
include("marblcrumb.class.php");

// search terms
$kw = $_GET["keyword"];
//$title = $_GET["title"];
$creator = $_GET["creator"];
$repo = $_GET["repository"];

// note: position & maxdisplay currently not in use (but probably should be)
$position = $_GET["pos"];    // position (i.e, cursor)
$maxdisplay = $_GET["max"];  // maximum  # results to display

// by default, search all 
$coll = "/db/FindingAids";
if (($repo != "all") && (in_array($repo, $collections))) {
      $coll .= "/$repo";
    }
// put quotes around collection for use in xquery collection statement
$coll = "'$coll'";


$url = "search.php?";
$args = array();
if ($kw) $args[] = "keyword=$kw";
if ($creator) $args[] .= "creator=$creator";
$url .= implode('&', $args);
//print "DEBUG: url is $url.<br>\n";
$crumbs = new marblCrumb("Search Results", $url); 
$crumbs->store();


// use eXist settings from config file
$connectionArray{"debug"} = false;
$xmldb = new xmlDbConnection($connectionArray);

//echo "<pre>";print_r($_GET);echo "</pre>";	


// if no position is specified, start at 1
if ($position == '') $position = 1;
// set a default maxdisplay
if ($maxdisplay == '') $maxdisplay = 50;       // what is a reasonable default?

// pull out exact phrase enclosed in quotation marks
preg_match_all("/\"([^\"]+)\"/", stripslashes($kw), $phrases);

$keywords = preg_replace("/\s*\"[^\"]+\"\s*/", "", $kw);

// clean up input & convert into an array
$kwarray = processterms($keywords);
$autharray = processterms($creator);



$doctitle = "Search Results";

html_head($doctitle);
include("template-header.inc");
print $crumbs;

// query to limit finding aids to irish subjects for delmas 
//$irishfilter = "controlaccess//subject |= 'irish ireland'";


$for = 'for $a in collection(' . $coll . ')/ead[' . $irishfilter . ']';
$let = "\n" . 'let $b := $a/eadheader
let $matchcount := text:match-count($a)';
$order = "order by \$matchcount descending";

// filters to add onto path in 'for' statement
$filter = "";
if ($keywords)
  $filter .= "[. &= \"$keywords\"]";
foreach ($phrases[1] as $p)
  $filter .= "[near(., '$p')]";
/*if ($repo != 'all')
 $filter .= "[eadheader/eadid/@mainagencycode = '$repo']";*/
  
//$where = "where \$a/archdesc
if ($creator) {
  // the simpler syntax "where x or y" should work here
  // in this case, that syntax caused the query not to match when it should
  $where = "
	where \$a/archdesc/did/origination[. &= \"$creator\"]
";
} 
/*	old creator search - used control access fields also
  $where = "
	where (\$a/archdesc/did/origination,
		\$a//controlaccess/persname[@encodinganalog='700'],
		\$a//controlaccess/corpname[@encodinganalog='710'],
		\$a//controlaccess/famname[@encodinganalog='700'])[. &= \"$creator\"]
";
} */

if ($title) $filter .= "[//titlestmt &=  '$title']";

// formerly used 'where' for conditions; now using filters on for statement

// put all search terms into an array for highlighting 
$myterms = array();
if ($mode == "exact") {
  array_push($myterms, $kw);
} else {
  if ($keywords != '') {$myterms = array_merge($myterms, $kwarray); }
  if (count($phrases[1])) {$myterms = array_merge($myterms, $phrases[1]); }
}

$return  = ' return
<record> {$a/@id}
  <name>
    {$a/archdesc/did/origination/persname}
    {$a/archdesc/did/origination/corpname}
    {$a/archdesc/did/origination/famname}
  </name>
  {$a/archdesc/did/unittitle}
  {$a/archdesc/did/physdesc}
  {$a/archdesc/did/abstract}
  {$a/archdesc/did/repository}';
// if this is a keyword search, return # of matches within the document
if ($kw) $return .= "\n" . '<matches><total>{$matchcount}</total></matches>' . "\n";


$xsl_file = "stylesheets/results.xsl";

$countquery = "<total>{count($for$filter $where return \$a)}</total>";
//$query = " <results>{ $countquery } { " . "$for$filter $let $order $where $return </record> " . "}</results>";
// exist automatically calculates the total number of matches
$query = " $for$filter $let $where $order $return </record> ";


$xmldb->xquery($query, $position, $maxdisplay); 
//$total = $xmldb->findNode("total");		// total # of matches, from count query
$total = $xmldb->count;	// total number of matches for this query
$xmldb->getCursor();

$xsl_file  = "stylesheets/results.xsl";

// pass search terms into xslt as parameters 
if ($kw != '')
  $xsl_params = array("url_suffix"  => "&keyword=$kw");

print '<div class="content">';

if ($total == 0){
 print "<p><b>No collections found.</b> You may want to broaden your search and see search tips for suggestions.</p>";
  include ("searchform.php");
} else {

  print "<div class='searchinfo'><h2 align='center'>Search Results</h2>";

  // # of documents found
  print "<p align='center'>Found <b>" . $total . "</b> collection";
  if ($total != 1) { print "s"; }


  // in phonetic mode, php highlighting will be inaccurate and/or useless... 
  // $xmldb->highlightInfo($myterms); 
  print "<p align=\"center\">where ";
  $useropts = array();
  if ($kw) array_push($useropts, "document contains \"" . stripslashes($kw) . "\"");
  if ($creator) array_push($useropts, "creator matches \"" . stripslashes($creator) . "\"");
  // FIXME: display selected repository here? if so, what wording / display name to use?
  //  if ($repo != 'all') array_push($useropts, "repository is $repo");
  print implode($useropts, " and ");
    "</p>"; 

  print "</div>";

  $opts = array();
  if ($kw) array_push($opts, "keyword=$kw");
  if ($creator) array_push($opts, "creator=$creator");
  $myopts = implode($opts, "&amp;");
  
  $xmldb->count = $total;	// set tamino count from first (count) query, so resultLinks will work
  $rlinks = $xmldb->resultLinks("search.php?$myopts", $position, $maxdisplay);
  print $rlinks;

  $xmldb->xslTransform($xsl_file, $xsl_params);
  $xmldb->printResult($myterms);
}

print $rlinks;
print '</div>';		// end of content div



include("template-footer.inc");
?>

</body>
</html>
