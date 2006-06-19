<?
//include_once("config.php");
//include_once("lib/xmlDbConnection.class.php");
include_once("common_functions.php");

//echo "<pre>";print_r($_REQUEST);echo "</pre>";


//$id = $_REQUEST['id'];


$connectionArray = array('host' => $tamino_server,
			 'db' => $tamino_db,
			 'coll' => $tamino_coll,
			 'debug' => false);

function getXMLContentsAsHTML($id, $element = "ead", $kw = null)
{
echo "function getXMLContentsAsHTML($id, $element)<hr>";
	global $crumbs;
	global $connectionArray;

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

	$kwarray = processterms($kw);
	
	//echo "<pre>"; print_r($kwarray); echo "</pre>";

	//	$element = (isset($_REQUEST['element'])) ? $_REQUEST['element'] : null;
	//$mode = ($element == 'did' || $element == 'c01') ? 'c-level-index' : 'summary';
	//$mode = 'table';
		
	$tamino = new xmlDbConnection($connectionArray);
	

	$declare = "declare namespace tf='http://namespaces.softwareag.com/tamino/TaminoFunction' ";

	$toc_query = "
		for \$z in input()/ead
		for \$a in \$z$path
		let \$ad := \$z/archdesc
		where \$a/@id='$id'  
		return 
			<toc>
				<ead>{\$z/@id}
					<name>
						{string(\$z/archdesc/did/origination/persname)}
						{string(\$z/archdesc/did/origination/corpname)}
						{string(\$z/archdesc/did/origination/famname)}
					</name>
					<eadheader>
						<filedesc><titlestmt>{\$z/eadheader/filedesc/titlestmt/titleproper}</titlestmt></filedesc>
					</eadheader>
					<archdesc>";

	if ($kw != '') {
	  $reflist = array();
	  $toc_query .= " <hits> { ";
	  for ($i=0; $i < count($kwarray); $i++) {
	    // count should include all nodes but the c01s, which are counted separately
	    $toc_query .= "let \$ref$i := tf:createTextReference(\$ad/*[not(c01)], '$kwarray[$i]')\n";
	    array_push($reflist, "\$ref$i");
	  }
	  $toc_query .= " return count((" . implode($reflist, ',') . ")) }
			</hits>";
	}

	$toc_query .= "

						<did>{\$ad/did/unittitle}</did>
						<dsc>
							{\$ad/dsc/head}
							{for \$c in \$ad/dsc/c01 ";
	if ($kw != '') {
	  $creflist = array();
	  for ($i=0; $i < count($kwarray); $i++) {
	    $toc_query .= "let \$ref$i := tf:createTextReference(\$c, '$kwarray[$i]')\n";
	    array_push($creflist, "\$ref$i");
	  }
	}
	$toc_query .= "
							 return 
							 <c01> 
								{\$c/@id} {\$c/@level}
								<did>
									{\$c/did/unittitle}
									{\$c/did/physdesc}
								</did>";
								//{-- adding c02 so c01 will display in xslt (kind of a hack) --}
								//<c02/> ";
	
	if ($kw != '') {
	  $toc_query .= "<hits>{count((" . implode($creflist, ',') . "))}</hits>\n";
	}
	$toc_query .= "

							</c01>}
						</dsc>
					</archdesc>
				</ead>
			</toc>
	";


	// addition to query for highlighting (when there are search terms)
	$hquery = "";
	$rval = "\$a";
	if ($kw) {
	  $refs = array();
	  for ($i=0; $i < count($kwarray); $i++) {
	    $hquery .= "let \$ref$i := tf:createTextReference(\$a, '$kwarray[$i]')\n";
	    array_push($refs, "\$ref$i");
	  }
	  $hquery .= "let \$allrefs := (" . implode($refs, ',') . ")\n";
	  $rval =  'tf:highlight($a, $allrefs, "MATCH")';
	  // all elements other than ead must be wrapped in an ead node
	}
	
	if ($wrapOutput) {
		$rval = "<ead>{ $rval }</ead>";
	}


	$query = "
		for \$z in input()/ead
		for \$a in \$z$path
		$hquery
		where \$a/@id='$id' 
		return $rval";

	
	$xsl_file 	= "html/stylesheets/marblfa.xsl";
	//$xsl_params = array('mode' => $mode);
	
	
	$xquery = "$declare <results>{ $toc_query } { $query }</results>";
	//echo "$xquery<hr>";
	$rval = $tamino->xquery(trim($xquery));
	$tamino->xslTransform($xsl_file, $xsl_params);
	
	
	$crumbs[2] = array ('anchor' => $tamino->findNode('name'));	
	
	return $tamino->xsl_result->saveXML();
}	
?>