<?php
include("config.php");
include("common_functions.php");
include_once("lib/xmlDbConnection.class.php");

$id = $_GET['id'];


// use tamino settings from config file
$args = array('host' => $tamino_server,
	      'db' => $tamino_db,
	      'coll' => $tamino_coll,
	      'debug' => false);

$tamino = new xmlDbConnection($args);

//echo "<pre>";print_r($_GET);echo "</pre>";	

// search terms
$kw = $_GET["keyword"];

$title = $_GET["title"];
$author = $_GET["author"];
$date = $_GET["date"];
$place= $_GET["place"];
$mode= $_GET["mode"];
$docid = $_GET["id"];		 // limit keyword search to one
$kwic = $_GET["kwic"];		 // is this a kwic search or not? defaults to not
$position = $_GET["pos"];    // position (i.e, cursor)
$maxdisplay = $_GET["max"];  // maximum  # results to display

// set some defaults
if ($kwic == '') $kwic = "false";
// if no position is specified, start at 1
if ($position == '') $position = 1;
// set a default maxdisplay
if ($maxdisplay == '') $maxdisplay = 10;       // what is a reasonable default?


$kwarray = processterms($kw);
$ttlarray = processterms($title);
$autharray = processterms($author);
$darray = processterms($date);
$plarray = processterms($place);

$doctitle = "Search Results";
$doctitle .= ($kwic == "true" ? " - Keyword in Context" : "");

html_head($doctitle);
print "<body>";
include("header.html");

$declare ='declare namespace tf="http://namespaces.softwareag.com/tamino/TaminoFunction" 
		   declare namespace xs="http://www.w3.org/2001/XMLSchema"';
$for = ' for $a in input()/ead';
if ($docid != '') { $for .= "[@id = '$docid']"; }
$let = 'let $b := $a/eadheader ';


// create an array of conditions for the query, depending on the search terms submitted
$conditions = array();

//Working queries. format: $where = "where tf:containsText(\$a, '$kw')";


/* Note: for counting & highlighting search results without matching
   text in the figure descriptions, it is necessary to make two
   separate text references-- one that will work for highlighting, and
   one that will give an accurate count (excluding text in figure
   descriptions).  */
if ($kw) {
    if ($mode == "exact") {
        array_push($conditions, "tf:containsText(\$a, '$kw')");
	$ref_let = "let \$ref := tf:createTextReference(\$a, '$kw') let \$allrefs := (\$ref)";
	$wordcount = count($kwarray);
    } else if ($mode == "synonym") {
        array_push($conditions, "tf:containsText(\$a, tf:synonym('$kw'))");
    } else {
      $all = 'let $allrefs := (';
      $allcount = 'let $allcounts := (';
      for ($i = 0; $i < count($kwarray); $i++) 
      {
		$term = ($mode == "phonetic") ? "tf:phonetic('$kwarray[$i]')" : "'$kwarray[$i]'";
		$let .= "let \$ref$i := tf:createTextReference(\$a, $term) ";
		
		if ($i > 0) { $all .= ", "; }
		$all .= "\$ref$i"; 
		
		array_push($conditions, "tf:containsText(\$a, $term)");
      }
      $all .= ") ";
      $let .= $all;
    }
}
if ($title) {
    foreach ($ttlarray as $t){
        array_push($conditions, "tf:containsText(\$b/filedesc/titlestmt, '$t') ");
    }
}
if ($author) {
        foreach ($autharray as $a){
	        array_push($conditions, "(tf:containsText(\$a/archdesc/did/origination/persname, '$a') 
	              						or tf:containsText(\$a/archdesc/did/origination/corpname, '$a') 
	              						or tf:containsText(\$a/archdesc/did/origination/famname, '$a')) 
	        						or 
        								(tf:containsText(\$a/archdesc/controlaccess/controlaccess/persname[@encodinganalog=\"700\"], '$a') 
  										or tf:containsText(\$a/archdesc/controlaccess/controlaccess/corpname[@encodinganalog=\"710\"], '$a') 
  										or tf:containsText(\$a/archdesc/controlaccess/controlaccess/famname[@encodinganalog=\"700\"], '$a')
  										) "
  			);
	    }
	   
}
if ($date) {
        foreach ($darray as $d){    
            array_push ($conditions, "tf:containsText(\$b/date, '$d') ");
    }
}
if ($place) {
    foreach ($plarray as $p){
    array_push ($conditions, "tf:containsText(\$b/pubPlace, '$p') ");
    }
}
foreach ($conditions as $c) {
    if ($c == $conditions[0]) {
        $where= "where $c";
    } else {
        $where.= " and $c";
            }
}

// put all search terms into an array for highlighting 
$myterms = array();
if ($mode == "exact") {
  array_push($myterms, $kw);
} else {
  if ($kw) {$myterms = array_merge($myterms, $kwarray); }
  if ($title) {$myterms = array_merge($myterms, $ttlarray); }
  if ($author) {$myterms = array_merge($myterms, $autharray); }
  if ($date) {$myterms = array_merge($myterms, $darray); }
  if ($place) {$myterms = array_merge($myterms, $plarray); }
}

//$return = ' return <record> {$a/@id} {$b} ' . "<total>{count($for $let $where return \$a)}</total>" . '</record>';
// for response-time testing without count


$return  = ' return';
$return .= ' <record> {$a/@id}';
$return .= ' <name>';
$return .= ' 	{$a/archdesc/did/origination/persname}';
$return .= ' 	{$a/archdesc/did/origination/corpname}';
$return .= ' 	{$a/archdesc/did/origination/famname}';
$return .= ' </name>';
$return .= ' {$a/archdesc/did/unittitle}';
$return .= ' {$a/archdesc/did/physdesc}';
$return .= ' {$a/archdesc/did/abstract}';



$countquery = "$declare <total>{count($for $let $where return \$a)}</total>";
$sort = 'sort by (name)';

$query = $declare . " <results><records>{ " . "$for $let $where $return </record> $sort" . "}</records></results>";
//$tamino->xquery($countquery);
//$total = $tamino->findNode("total");
//$tamino->xquery($query);
//$tamino->getXqueryCursor();

$xsl_file = "stylesheets/results.xsl";

// numbers are based on keyword match; only include if keyword terms are part of the search
if ($kw) {
  if ($mode == "exact") {   
    /* note: in exact mode, Tamino still tokenizes the text references, so count is off for the phrase (e.g., one match for a 4-word phrase counts as 4);
       this divide-by-wordcount correctly calculates the number of occurrences of the entire phrase. */
    $return .= "<matches><total>{xs:integer(count(\$allrefs) div $wordcount)}</total>"; 
  } else { $return .= '<matches><total>{count($allrefs)}</total>'; }
  if ($mode != "exact") {	// exact mode - treat string as a phrase, not multiple terms
    if (count($kwarray) > 1) {	// if there are multiple terms, display count for each term
      for ($i = 0; $i < count($kwarray); $i++) {
        $return .= "<term>$kwarray[$i]<count>{count(\$ref$i)}</count></term>";
      }
    }
  }
  $return .= '</matches>';
}

// if this is a keyword in context search, get context nodes
// return previous pagebreak (get closest by max of previous sibling pb & previous p/pb)
if ($kwic == "true") {
  $return .= '<context><page>{tf:highlight($a//p[';
  if ($mode == "exact") { 
    $return .= "tf:containsText(.//text()[not(parent::figDesc)], '$kw')"; 
  } else {
    for ($i = 0; $i < count($kwarray); $i++) { 
      $term = ($mode == "phonetic") ? "tf:phonetic('$kwarray[$i]')" : "'$kwarray[$i]'";
      if ($i > 0) { $return .= " or "; }
      $return .= "tf:containsText(.//text()[not(parent::figDesc)], $term) ";
    }
  }
  $return .= '], $allrefs, "MATCH")}</page></context>';
}
//$return .= '</record>';
//$order = 'order by $b/author'; 
// order results by relevance


/* let $pbsib := $p/preceding-sibling::pb/@n
 let $psib := $p/preceding-sibling::p/pb/@n
 let $seq := ($pbsib, $psib)
let $pb := max($seq)  
*/

//$sort = 'sort by (author)';
if ($kw) {	// only sort by # of matches if it is defined
   $sort = 'sort by (xs:int(matches/total) descending)';
}

$countquery = "$declare <total>{count($for $let $where return \$a)}</total>";
$query = $declare . " <results>{ " . "$for $let $ref_let $where $return </record> $sort" . "}</results>";

// first, get the count for number matching
$tamino->xquery($countquery);
$total = $tamino->findNode("total");

$tamino->xquery($query, $position, $maxdisplay); 
$tamino->getCursor();

$xsl_file  = "stylesheets/results.xsl";
$kwic_xsl  = "kwic.xsl";
$kwic1_xsl = "kwic-towords.xsl";
$kwic2_xsl = "kwic-words.xsl";

// pass search terms into xslt as parameters 
// (xslt passes on terms to browse page for highlighting)
$term_list = implode("|", $myterms);
$xsl_params = array("term_list"  => $term_list);

print '<div class="content">';

if ($total == 0){
 print "<p><b>No matches found.</b> You may want to broaden your search and see search tips for suggestions.</p>";
  include ("searchoptions.php");
} else {

  print "<h2 align='center'>" . ($kwic == "true" ? "Keyword in Context " : "") . "Search Results</h2>";


  if (!($docid)) {
    // only display # of results if we are looking at more than one document
    print "<p align='center'>Found <b>" . $total . "</b> match";
    if ($exist->count != 1) { print "es"; }
    // sort is only operative when keywords are included in search terms
    if ($kw) {
      print ". Results sorted by relevance.</p>"; 
    }
  }

  $myopts = "keyword=$kw&title=$title&author=$author&date=$date&place=$place&mode=$mode";
  // based on KWIC mode, set options for search link & transform result appropriately
  switch ($kwic) {
     case "true": $altopts = "$myopts&pos=$position&max=$maxdisplay&kwic=false";
 	    	$mylink = "Summary"; 
	        $myopts .= "&kwic=true";	// preserve for result links
		$tamino->xslTransform($kwic1_xsl);
		//		print "DEBUG: went through one transform.";
		//		  $tamino->displayXML(1);
		$tamino->xslTransformResult($kwic2_xsl);
		//		print "DEBUG: went through second transform.";
		//$tamino->displayXML(1);
		$xsl_params{"mode"} = "kwic";
		$tamino->xslTransformResult($xsl_file, $xsl_params);
		break;
     case "false": $altopts .= "$myopts&pos=$position&max=$maxdisplay&kwic=true";
		$mylink = "Keyword in Context"; 
		$xsl_params{"selflink"} = "search.php?$myopts";
		$tamino->xslTransform($xsl_file, $xsl_params);
		break;
  }

  // in phonetic mode, php highlighting will be inaccurate and/or useless... 
  //if ($mode != "phonetic") { $tamino->highlightInfo($myterms); }
  if ($mode != "phonetic") { echo "<p align=\"center\">Search Terms: ". join(" ", $myterms) ." </p>"; }

  $tamino->count = $total;	// set tamino count from first (count) query, so resultLinks will work
  //$rlinks = $tamino->resultLinks("search.php?$myopts", $position, $maxdisplay);
  //print $rlinks;

  // kwic/summary results toggle only relevant if search includes keywords
  /*
  if ($kw) {
    print "<p>View <a href='search.php?$altopts'>$mylink</a> search results. </p>";
  }
  */

  if ($kwic == "true") {
    print "<p class='tip'>Page numbers indicate where paragraphs containing search terms begin.</p>";
  }

  $tamino->printResult($myterms);
}

print "<p>" . $rlinks . "</p>";
print '</div>';		// end of content div


//Function that takes multiple terms separated by white spaces and puts them into an array
function processterms ($str) {
// clean up input so explode will work properly
    $str = preg_replace("/\s+/", " ", $str);  // multiple white spaces become one space
    $str = preg_replace("/\s$/", "", $str);	// ending white space is removed
    $str = preg_replace("/^\s/", "", $str);  //beginning space is removed
    $terms = explode(" ", $str);    // multiple search terms, divided by spaces
    return $terms;
}


include("footer.html");
?>

</body>
</html>
