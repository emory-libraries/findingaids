<?
include_once("config.php");
include_once("lib/xmlDbConnection.class.php");
include_once("common_functions.php");
include("marblcrumb.class.php");


$id = $_GET["id"];
$element = $_GET["el"];
$kw = $_GET["keyword"];


if (empty($element)) {
  $element = "ead";		// default element to retrieve
 } else if (!($element == "c01" || $element ==  "c02" || $element == "c03"
	      || $element == "did" || $element == "ead")) {
  // make sure that the element is something we expect
  print "DEBUG: element $el not expected, quitting.\n";
  // FIXME: add a better error message here
  exit();
 }




$connectionArray{"debug"} = false;

 

//echo "<pre>";print_r($_REQUEST);echo "</pre>";


	// determine xpath for query according to element
	switch ($element)
	{
		case 'c01':
		  $path = "/archdesc/dsc/c01";
		  $mode = 'c-level-index';
		  $wrapOutput = true;
		  break;
		
		case 'c02':
		  $path = "/archdesc/dsc/c01/c02";
		  $mode = 'c-level-index';
		  $wrapOutput = true;
		break;

		case 'c03':
		  $path = "/archdesc/dsc/c01/c02/c03";
		  $mode = 'c-level-index';
		  $wrapOutput = true;
		break;

		case 'did':
		  $path = "/archdesc/did";
		  $mode = 'c-level-index';
		  $wrapOutput = true;
		break;
		
		case 'ead':
		default:
		  // query for all volumes 
		  $path = "";
		  $mode = 'summary';
		  
		  $wrapOutput = false;
	}

	//$kwarray = processterms($kw);
	// keyword is being passed in as a | delimited string
	$kwarray = array();
	$phrases = array();
	$keywords = "";
	foreach (explode('|', $kw) as $k) {
	  if (preg_match("/_/", $k)) {
	    $k = preg_replace("/_/", " ", $k);
	    array_push($phrases, $k);
	  } else {
	    array_push($kwarray, $k);
	    $keywords .= " $k";
	  }
	}
	  //	$kwarray = explode('|', $kw);
	  //	$kw = preg_replace("/\|/", " ", $kw);  // multiple white spaces become one space
	
	//echo "<pre>"; print_r($kwarray); echo "</pre>";

	//	$element = (isset($_REQUEST['element'])) ? $_REQUEST['element'] : null;
	//$mode = ($element == 'did' || $element == 'c01') ? 'c-level-index' : 'summary';
	//$mode = 'table';
		
	$tamino = new xmlDbConnection($connectionArray);
	
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

	// note: the filter is at the top-level, since the item we are returning (c01, etc.)
	// may or may not include the search terms, but should be returned either way
	$toc_query = "
		let \$a := /ead${orfilter}${path}[@id = '$id']
		let \$doc := root(\$a)/ead
		let \$ad := \$doc/archdesc 
		return 
			<toc>
				<ead>{\$doc/@id}
					<name>
						{string(\$doc/archdesc/did/origination/persname)}
						{string(\$doc/archdesc/did/origination/corpname)}
						{string(\$doc/archdesc/did/origination/famname)}
					</name>
					<eadheader>
						<filedesc><titlestmt>{\$doc/eadheader/filedesc/titlestmt/titleproper}</titlestmt></filedesc>
					</eadheader>
					<archdesc>
						<did>{\$ad/did/unittitle}"; 
	if ($kw != '') {
	  $toc_query .= " <hits> { let \$didm := \$ad/did$orfilter
			return text:match-count(\$didm) }</hits>";
	}

	$toc_query .= "
						</did>";
	// hit counts for top-level table of contents items;
	// sum up multiple counts where the count needs to include multiple nodes
	if ($kw != '') {
	  $toc_query .= "<collectiondescription>
			    <hits> { sum(for \$cdm in (\$ad//bioghist,\$ad//scopecontent)$orfilter
			    return text:match-count(\$cdm)) }</hits>
			 </collectiondescription>
			 <controlaccess>
			    <hits> { sum(for \$cam in \$ad//controlaccess$orfilter
			    return text:match-count(\$cam)) }</hits>
			 </controlaccess>
		";
	}
	$toc_query .= "
						<dsc>
							{\$ad/dsc/head}";
	if ($kw != '') {
	  $toc_query .= "<hits>{let \$dscm := \$ad/dsc$orfilter return text:match-count(\$dscm) }</hits>";
	}
	$toc_query .= "
							{for \$c in \$ad/dsc/c01[@level='series']
							 let \$cmatch := \$c$orfilter
							 return  
							 <c01> 
								{\$c/@id} {\$c/@level}
								{if (exists(\$c/c02)) then <c02/> else ()}\n";
	if ($kw != '') { 
	  $toc_query .= "<hits>{text:match-count(\$cmatch)}</hits>\n";
	} 
	$toc_query .= "
								<did>
									{\$c/did/unitid}
									{\$c/did/unittitle}
									{\$c/did/physdesc}
								</did>
							</c01>}
						</dsc>
					</archdesc>
				</ead>
			</toc>
	";


	// addition to query for highlighting (when there are search terms)
	$hquery = "";
	$rval = "\$a";
	if ($kw != '') { 
	  $hitcount .= "{let \$m := \$c01$orfilter return <hits>{text:match-count(\$m)}</hits>}\n";
	}

	if ($element == "ead") {		// return only necessary sections, not the entire document
		  $rval = "<ead>{\$a/@id}
		  {\$a/eadheader}
		  {\$a/frontmatter}
		 <archdesc>
		  {\$a/archdesc/*[not(self::dsc)]}
		  {for \$d in \$a/archdesc/dsc
		   return <dsc> {\$d/@*}
		   {\$d/head}
		   {for \$i in \$d/c01[@level!='series']
		    return if (exists(\$i$orfilter))
			  then \$i$orfilter
			else \$i }
		   {for \$c01 in \$d/c01[c02]
		    return <c01>
		      {\$c01/@*}
		      {\$c01/did}
		       $hitcount
		      {for \$c02 in \$c01/c02[@level='subseries']
			return <c02>
				{\$c02/@*}
				{\$c02/did}
				{let \$m2 := \$c02$orfilter
				  return <hits>{text:match-count(\$m2)}</hits>}
			      {for \$c03 in \$c02/c03[c04]
				return <c03>{\$c03/@*}
					{\$c03/did}
					{let \$m3 := \$c03$orfilter
					  return <hits>{text:match-count(\$m3)}</hits>}
				       </c03>}
			      </c02> }
		     </c01> }
		     </dsc>} 
		 </archdesc></ead> ";
	}


	// all elements other than ead must be wrapped in an ead node
	if ($wrapOutput) {
	  // return parent c01 id so we can highlight current section in table of contents
		$rval = "<ead>{ $rval } <parent id='{\$a/ancestor::c01/@id}'/></ead>";
		       
	}


	/*	$query = "
		for \$doc in input()/ead
		for \$a in \$doc$path
		$hquery
		where \$a/@id='$id' 
		return $rval";
	*/

	// section may or may not contain keywords; return with highlighting if it does
	$query = "let \$i := /ead${path}[@id = '$id'] ";
	if ($kw != '')
	  $query .= "let \$im := \$i$orfilter
		  let \$a := (if (exists(\$im)) then
		      \$im
		  else  \$i)
		  return $rval";
	else
	  $query .= "let \$a := \$i
		     return $rval";
	//		  return if (exist$rval";

	$xsl_file 	= "stylesheets/marblfa.xsl";
	// xslt passes on keywords to subsections of document via url
	$term_list = urlencode(implode("|", array_merge($kwarray, $phrases)));
if ($kw != '') 
  $xsl_params = array("url_suffix"  => "&keyword=$kw");
	
	
	//$xquery = "$declare <results>{ $toc_query } { $query }</results>";
	$xquery = "<results>{ $toc_query } { $query }</results>";
	//echo "$xquery<hr>";
	$rval = $tamino->xquery(trim($xquery));
	$tamino->xslTransform($xsl_file, $xsl_params);
	

	$docname = $tamino->findNode('unittitle');
	$pagename = $docname;
//	$crumbs[2] = array ('anchor' => $docname);
	$htmltitle = "$docname";
if ($element != "ead") {
  $pagename = $tamino->findNode("results/ead/$element//unittitle");
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
$tamino->printResult();
print '</div>';

include("template-footer.inc");
	
?>