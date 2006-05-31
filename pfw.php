<?
include "html/common_functions.php";

$url_qs = key($_REQUEST);
//echo "url_qs=$url_qs<hr>";

//$pattern = '/(.*)(-)(.*)*/';
//preg_match($pattern, $url_qs, $matches) > 0;
//list($devnull, $cmd, $devnull, $id) = $matches;
//echo "<pre>"; print_r($matches); echo "</pre>";

$redirectURL = "http://biliku.library.emory.edu/jbwhite/projects/marblfa-php/";

$cmd = split('-', $url_qs);
//echo "<pre>"; print_r($_SERVER); echo "</pre>";
//exit;

$crumbs = $_SESSION['crumb'];

echo "<pre>"; print_r($crumbs); echo "</pre>";

$crumbs[0] = array ('href' => 'http://marbl.library.emory.edu', 'anchor' => 'MARBL Finding Aids');

switch ($cmd[0])
{
	case 'banner':
		$f = "html/". $cmd[1] .".html";
	break;
	
	case 'tamino': 
		$crumbs[2] = array ('href' => $_REQUEST['QUERY_STRING'], 'anchor' => 'Finding Aid');	
		
		$toc = "section-toc-".end($cmd);
		$content = "section-content-".end($cmd);
	
		include("template-header.inc");
		include ("html/result.php");
		include("template-footer.inc");		
	break;
	
	case 'browse':
		
		$crumbs[1] = array ('href' => 'browse', 'anchor' => 'Browse');
		
		$f = "html/browse.php?l=".$cmd[2];
		$content = file_get_contents($redirectURL . $f);
		$left_nav = "";
		
		include("template-header.inc");
		include("template.php");
		include("template-footer.inc");
	break;
	
	case 'rqst':
		$f = "html/searchoptions.php?";
		$content = file_get_contents($redirectURL . $f);

		include("template-header.inc");
		include("template.php");
		include("template-footer.inc");
	break;

	case 'search':				
		foreach($_REQUEST as $k => $v)
		{
			$qs .= "&$k=" . encode_url($v);
		}
		$f = "html/search.php?1=1" . $qs;
		$content = file_get_contents($redirectURL . $f);
		
		include("template-header.inc");
		include("template.php");
		include("template-footer.inc");
	break;	
	
	case 'section':		
		switch ($cmd[1])
		{
			case 'toc':
				$f = "html/toc.php?id=".end($cmd);
				readfile($redirectURL . $f);
			break;
			
			case 'content':			
				$e = (count($cmd) > 3) ? $cmd[2] : '';
				$f = "html/content.php?element=$e&id=".end($cmd);
				readfile($redirectURL . $f);	
			break;
		}
	break;
	
	default:
		exit;
}

$_SESSION['crumb'] = $crumbs;
?>