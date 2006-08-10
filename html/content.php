<?
//include_once("config.php");
//include_once("lib/xmlDbConnection.class.php");
include_once("common_functions.php");

//echo "<pre>";print_r($_REQUEST);echo "</pre>";


//$id = $_REQUEST['id'];


function getXMLContentsAsHTML($id, $element = "ead", $kw = null)
{
echo "function getXMLContentsAsHTML($id, $element)<hr>";
	global $crumbs;
	global $htmltitle;
	global $connectionArray;

	$connectionArray{"debug"} = false;
	
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
	if ($keywords != ' ' and $keywords != '') array_push($filter, ". &= '$keywords'");
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
					<archdesc>";

	if ($kw != '') {
	  //	  $toc_query .= " <hits> { text:match-count(\$ad/*[not(c01)]) }</hits>";
	  $toc_query .= " <hits> { let \$adm := \$ad$orfilter
			return text:match-count(\$adm) }</hits>";
	}

	$toc_query .= "

						<did>{\$ad/did/unittitle}</did>
						<dsc>
							{\$ad/dsc/head}
							{for \$c in \$ad/dsc/c01[@level='series']
							 let \$cmatch := \$c$orfilter
							 return  
							 <c01> 
								{\$c/@id} {\$c/@level}\n";
	if ($kw != '') { 
	  $toc_query .= "<hits>{text:match-count(\$cmatch)}</hits>\n";
	} 
	$toc_query .= "
								<did>
									{\$c/did/unitid}
									{\$c/did/unittitle}
									{\$c/did/physdesc}
								</did>
								{for \$c2 in \$c/c02 return <c02>{\$c2/@id}</c02>}
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
		   {for \$c01 in \$d/c01[c02]
		    return <c01>
		      {\$c01/@*}
		      {\$c01/did}
		      <c02/>
		       $hitcount
		     </c01> }
		     </dsc>} 
		 </archdesc></ead> ";
	}


	// all elements other than ead must be wrapped in an ead node
	if ($wrapOutput) {
		$rval = "<ead>{ $rval }</ead>";
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
	  $query .= "return $rval";
	//		  return if (exist$rval";

	$xsl_file 	= "html/stylesheets/marblfa.xsl";
	// xslt passes on keywords to subsections of document via url
	$term_list = urlencode(implode("|", array_merge($kwarray, $phrases)));
	$xsl_params = array("url_suffix"  => "-kw-$term_list");
	
	
	//$xquery = "$declare <results>{ $toc_query } { $query }</results>";
	$xquery = "<results>{ $toc_query } { $query }</results>";
	//echo "$xquery<hr>";
	$rval = $tamino->xquery(trim($xquery));
	$tamino->xslTransform($xsl_file, $xsl_params);
	

	$docname = $tamino->findNode('name');
	$crumbs[2] = array ('anchor' => $docname);
	$htmltitle .= ": $docname";
	if ($element != "ead") 
	  $htmltitle .= " [" . $tamino->findNode("results/ead/$element//unittitle") . "]";
	
	return $tamino->xsl_result->saveXML();
}	
?>