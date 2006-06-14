<?
//include_once("config.php");
//include_once("lib/xmlDbConnection.class.php");
//include("common_functions.php");

//echo "<pre>";print_r($_REQUEST);echo "</pre>";


//$id = $_REQUEST['id'];

function getXMLContentsAsHTML($connectionArray, $id)
{
	global $crumbs;
	
	$element = (isset($_REQUEST['element'])) ? $_REQUEST['element'] : null;
	//$mode = ($element == 'did' || $element == 'c01') ? 'c-level-index' : 'summary';
	//$mode = 'table';
		
	$tamino = new xmlDbConnection($connectionArray);
	
	
	$toc_query = "
		for \$a in input()/ead 
		let \$ad := \$a/archdesc
		where \$a/@id='$id' 
		return 
			<toc>
				<ead>{\$a/@id}
					<name>
						{string(\$a/archdesc/did/origination/persname)}
						{string(\$a/archdesc/did/origination/corpname)}
						{string(\$a/archdesc/did/origination/famname)}
					</name>
					<eadheader>
						<filedesc><titlestmt>{\$a/eadheader/filedesc/titlestmt/titleproper}</titlestmt></filedesc>
					</eadheader>
					<archdesc>
						<did>{\$ad/did/unittitle}</did>
						<dsc>
							{\$ad/dsc/head}
							{for \$c in \$ad/dsc/c01 
							 return 
							 <c01> 
								{\$c/@id} {\$c/@level}
								<did>
									{\$c/did/unittitle}
									{\$c/did/physdesc}
								</did>
								{-- adding c02 so c01 will display in xslt (kind of a hack) --}
								<c02/>
							</c01>}
						</dsc>
					</archdesc>
				</ead>
			</toc>
	";
	
	
	switch ($element)
	{
		case 'c01':
			$query = "
				for \$a in input()/ead/archdesc/dsc/c01 
				where \$a/@id='$id' 
				return <ead>{\$a}</ead>
			";		
			$mode = 'c-level-index';
		break;
		
		case 'c02':
			$query = "
				for \$a in input()/ead/archdesc/dsc/c01/c02 
				where \$a/@id='$id' 
				return <ead>{\$a}</ead>
			";		
			$mode = 'c-level-index';
		break;
			
		case 'did':
			$query = "
				for \$a in input()/ead/archdesc/did
				where \$a/@id='$id' 
				return <ead>{\$a}</ead>
			";		
			$mode = 'c-level-index';
		break;
		default:
			// query for all volumes 
			$query = "
				for \$a in input()/ead 
				where \$a/@id='$id' 
				return \$a
			";
			$mode = 'summary';
	}
	
	$xsl_file 	= "html/stylesheets/marblfa.xsl";
	//$xsl_params = array('mode' => $mode);
	
	
	$xquery = "<results>{ $toc_query } { $query }</results>";
	//echo "$xquery<hr>";
	$rval = $tamino->xquery(trim($xquery));
	$tamino->xslTransform($xsl_file, $xsl_params);
	
	
	$crumbs[2] = array ('anchor' => $tamino->findNode('name'));	
	
	return $tamino->xsl_result->saveXML();
}	
?>