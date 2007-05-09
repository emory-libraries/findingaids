<?
include_once("config.php");
include_once("lib/xmlDbConnection.class.php");
include_once("common_functions.php");
include("marblcrumb.class.php");

$connectionArray{"debug"} = false;


$id = $_GET["id"];
if (isset($_GET["el"])) 
  $element = $_GET["el"];
$kw = $_GET["keyword"];

$acceptable_els = array("c01", "c02", "c03", "did", "ead", "index");

if (empty($element)) {
  $element = "ead";		// default element to retrieve
  $mode = "summary";
 } else if (! in_array($element, $acceptable_els)) {
  // make sure that the element is something we expect
  print "Error: element <b>$element</b> not expected, quitting.\n";
  // FIXME: add a better error message here?
  exit();
 }


 
//$kwarray = processterms($kw);
// keyword is being passed in as a | delimited string
$kwarray = array();
$phrases = array();
$keywords = "";
foreach (explode('|', $kw) as $k) {
  if (preg_match("/_/", $k)) {
    $k = preg_replace("/_/", " ", $k);
    array_push($phrases, addslashes($k));
  } else {
    array_push($kwarray, $k);
    $keywords .= " " . addslashes($k);
  }
}


$xmldb = new xmlDbConnection($connectionArray);
	
// using filters to restrict element path in 'for' statement
$filter = array();
// only add a keyword filter if there are keywords defined
if ($keywords != ' ' and $keywords != '') array_push($filter, ". |= '$keywords'");
foreach ($phrases as $p)
// eXist's near function finds the terms in this order, by default 1 word away
// (it does, however count & match every occurrence of the terms in the phrase)
  array_push($filter, "near(., '$p')");

// using an "or" filter to highlight any of the search terms that occur in any section of the document
if (count($filter)) {	// keyword/phrase mode (at least one filter)
  $orfilter = "[" . implode(" or ", $filter) . "]";
 } else {
  $orfilter = "";
 }

// pull out exact phrase enclosed in quotation marks
preg_match_all("/\"([^\"]+)\"/", stripslashes($kw), $phrases);
$phrase = $phrases[1][0];

$keywords = preg_replace("/\s*\"[^\"]+\"\s*/", "", $kw);



//$xquery = $eadxq . 'let $a := ' . "/ead${orfilter}${path}[@id = '$id'] " . '
$xquery = $eadxq . "\n" .  'let $a := ' . "//${element}[@id = '$id'] " . '
let $ead := root($a)/ead  
return <results> 
   {eadxq:toc($ead, "' . $keywords . '", "' . $phrase . '") } 
   {eadxq:content($a, "' . $keywords . '", "' . $phrase . '")} 
</results>';
// note: doesn't yet handle highlighting, hit counts completely 
  


$xsl_file = "stylesheets/marblfa.xsl";

// xslt passes on keywords to subsections of document via url
$term_list = urlencode(implode("|", array_merge($kwarray, $phrases)));
if ($kw != '') 
  $xsl_params = array("url_suffix"  => "&keyword=$kw");
	
//$xquery = "$declare <results>{ $toc_query } { $query }</results>";
//$xquery = "$declare <results>{ $toc_query } { $query }</results>";
//echo "$xquery<hr>";
$rval = $xmldb->xquery(trim($xquery));
$xmldb->xslTransform($xsl_file, $xsl_params);


// get unittitle, but add spaces before any unitdates 
$docname = $xmldb->findNode('archdesc/did/unittitle/text()');
if ($ud = $xmldb->findNode('archdesc/did/unittitle/unitdate[1]'))
  $docname .= " " . $ud;
if ($ud = $xmldb->findNode('archdesc/did/unittitle/unitdate[2]'))
  $docname .= " " . $ud;
//$docname = $xmldb->findNode('archdesc/did/unittitle/text()'); 

	$pagename = $docname;
//	$crumbs[2] = array ('anchor' => $docname);
	$htmltitle = "$docname";
if ($element == 'index') {
  $pagename = $xmldb->findNode("results/ead/$element/head");
  $htmltitle .= " [$pagename]";
} else if ($element != "ead") {
  $pagename = $xmldb->findNode("results/ead/$element//unittitle");
  $htmltitle .= " [$pagename]";
 }

// build url for breadcrumb
$url = "content.php?";
$args = array();
if ($element && $element != 'ead') $args[] = "el=$element";
if ($id) $args[] = "id=$id";
if ($kw) $args[] = "keyword=$kw";
$url .= implode('&', $args);
$crumbs = new marblCrumb($pagename, $url); 
$crumbs->store();



html_head("Finding Aid : $htmltitle");
include("template-header.inc");
print $crumbs;

print '<div class="content">';
$xmldb->printResult();
print '</div>';

include("template-footer.inc");
	
?>