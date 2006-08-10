<?php
include("config.php");
include("common_functions.php");
include_once("lib/xmlDbConnection.class.php");

// use eXist settings from config file
$connectionArray{"debug"} = false;
$tamino = new xmlDbConnection($connectionArray);

//echo "<pre>";print_r($_GET);echo "</pre>";	

// search terms
$kw = $_GET["keyword"];
$title = $_GET["title"];
$author = $_GET["author"];
//$date = $_GET["date"];
//$place= $_GET["place"];
//$mode= $_GET["mode"];
//$docid = $_GET["id"];		 // limit keyword search to one document

// note: position & maxdisplay currently not in use
$position = $_GET["pos"];    // position (i.e, cursor)
$maxdisplay = $_GET["max"];  // maximum  # results to display

// if no position is specified, start at 1
if ($position == '') $position = 1;
// set a default maxdisplay
if ($maxdisplay == '') $maxdisplay = 10;       // what is a reasonable default?

// pull out exact phrase enclosed in quotation marks
preg_match_all("/\"([^\"]+)\"/", stripslashes($kw), &$phrases);

$keywords = preg_replace("/\s*\"[^\"]+\"\s*/", "", stripslashes($kw));

// clean up input & convert into an array
$kwarray = processterms($keywords);
$autharray = processterms($author);



$doctitle = "Search Results";

html_head($doctitle);
print "<body>";
include("header.html");

$for = ' for $a in /ead';
$let = "\n" . 'let $b := $a/eadheader
let $matchcount := text:match-count($a)';
$order = 'order by $matchcount descending';

// filters to add onto path in 'for' statement
$filter = "";
if ($keywords)
  $filter .= "[. &= '$keywords']";
foreach ($phrases[1] as $p)
  $filter .= "[near(., '$p')]";	
if ($author) {
  $filter .= "[archdesc/did/origination &= '$author' or
 	       (//controlaccess/persname[@encodinganalog='700'] &= '$author'
		or //controlaccess/corpname[@encodinganalog='710'] &= '$author'
		or //controlaccess/famname[@encodinganalog='700'] &= 'author')]";
}

if ($title) $filter .= "[//titlestmt &=  '$title']";

// formerly used 'where' for conditions; now using filters on for statement
$where = '';

// put all search terms into an array for highlighting 
$myterms = array();
if ($mode == "exact") {
  array_push($myterms, $kw);
} else {
  if ($keywords != '') {$myterms = array_merge($myterms, $kwarray); }
  if (count($phrases[1])) {$myterms = array_merge($myterms, $phrases[1]); }
  if ($title) {$myterms = array_merge($myterms, $ttlarray); }
  //  if ($author) {$myterms = array_merge($myterms, $autharray); }
  if ($date) {$myterms = array_merge($myterms, $darray); }
  if ($place) {$myterms = array_merge($myterms, $plarray); }
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
  {$a/archdesc/did/abstract}';
// if this is a keyword search, return # of matches within the document
if ($kw) $return .= "\n" . '<matches><total>{$matchcount}</total></matches>' . "\n";


$xsl_file = "stylesheets/results.xsl";

$countquery = "<total>{count($for$filter $where return \$a)}</total>";
//$query = " <results>{ $countquery } { " . "$for$filter $let $order $where $return </record> " . "}</results>";
// exist automatically calculates the total number of matches
$query = " $for$filter $let $order $where $return </record> ";


$tamino->xquery($query, $position, $maxdisplay); 
//$total = $tamino->findNode("total");		// total # of matches, from count query
$total = $tamino->count;	// total number of matches for this query
$tamino->getCursor();

$xsl_file  = "stylesheets/results.xsl";

// pass search terms into xslt as parameters 
// (xslt passes on terms to browse page for highlighting)
$term_list = urlencode(implode("|", $myterms));
// only pass keywords, not creator search terms
if ($term_list != '')
    $xsl_params = array("url_suffix"  => "-kw-$term_list");

print '<div class="content">';

if ($total == 0){
 print "<p><b>No collections found.</b> You may want to broaden your search and see search tips for suggestions.</p>";
  include ("searchoptions.php");
} else {

  print "<div class='searchinfo'><h2 align='center'>Search Results</h2>";

  // # of documents found
  print "<p align='center'>Found <b>" . $total . "</b> collection";
  if ($total != 1) { print "s"; }


  // in phonetic mode, php highlighting will be inaccurate and/or useless... 
  // $tamino->highlightInfo($myterms); 
  print "<p align=\"center\">where ";
  if ($kw) print "document contains '" . stripslashes($kw) . "'";
  if ($kw && $author) print " and ";
  if ($author) print "creator matches \"$author\"";
    "</p>"; 

  print "</div>";
  
  $tamino->count = $total;	// set tamino count from first (count) query, so resultLinks will work
  //$rlinks = $tamino->resultLinks("search.php?$myopts", $position, $maxdisplay);
  //print $rlinks;

  $tamino->xslTransform($xsl_file, $xsl_params);
  $tamino->printResult($myterms);
}

//print "<p>" . $rlinks . "</p>";
print '</div>';		// end of content div



include("footer.html");
?>

</body>
</html>
