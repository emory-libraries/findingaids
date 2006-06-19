<?
include_once("html/config.php");
include_once("html/lib/xmlDbConnection.class.php");
include("html/common_functions.php");

$url_qs = key($_REQUEST);
//echo "url_qs=$url_qs<hr>";

//Set Pattern to match against URL must have corresponding switch case below
$pattern[0] = '/(browse)(-coll-)?(.*)/';
$pattern[1] = '/(tamino)-(.*)(-kw-)(.*)/';
$pattern[2] = '/(tamino)-(.*)/';
$pattern[3] = '/(rqst)/';
$pattern[4] = '/(search)/';
$pattern[5] = '/(section-content)-(c0[12])?-?(.*)(-kw-)(.*)/';
$pattern[6] = '/(section-content)-(c0[12])?-?(.*)/';

$i = 0;
//$matches = null;
do 
{
	preg_match($pattern[$i], $url_qs, $matches) > 0;
	$i++;	
} while (empty($matches) && $i < count($pattern));
$cmd = $matches[1];

echo "<pre>"; print_r($matches); echo "</pre><p>";


$dir = split('/', $_SERVER['SCRIPT_URI']);
array_pop($dir); //drop the last field from the array which contains the filename
$redirectURL = join("/", $dir) . "/";

session_start();
$crumbs = $_SESSION['crumb'];

$crumbs[0] = array ('href' => 'http://marbl.library.emory.edu/FindingAids/index.html', 'anchor' => 'MARBL Finding Aids');
//echo "<pre>"; print_r($crumbs); echo "</pre>";
switch ($cmd)
{
	case 'banner':
		$f = "html/". $cmd[1] .".html";
	break;
	
	case 'section-content':			
	case 'tamino': 
		if($cmd == 'section-content') 
		{
			$element = $matches[2];
			$id 	 = $matches[3];
			$kw 	 = $matches[5];
		} else {
			$id = $matches[2];
			$kw = $matches[4];
		}
		if ($element == "") $element = "ead";
	
		$htmltitle = "Finding Aid";
		
		include("html/content.php");		
		
		$content = getXMLContentsAsHTML($id, $element, $kw);
		html_head($htmltitle);
				

	break;
	
	case 'browse':
		
		$crumbs[1] = array ('href' => $url_qs, 'anchor' => 'Browse');
		$crumbs[2] = null;
		$htmltitle = "Browse - Collections";
		if (end($matches)) $htmltitle .= " (" . end($matches) . ")";
		html_head($htmltitle);
		$f = "html/browse.php?l=".end($matches);
		$content = file_get_contents($redirectURL . $f);
		
	break;
	
	case 'rqst':
		$crumbs[1] = array ('href' => 'rqst', 'anchor' => 'Search');
		$crumbs[2] = null;
				
		html_head("Search - Finding Aids");
		$f = "html/searchoptions.php?";
		$content = file_get_contents($redirectURL . $f);

	break;

	case 'search':		
		$crumbs[1] = array ('href' => 'rqst', 'anchor' => 'Search');
		$crumbs[2] = null;
	
		foreach($_REQUEST as $k => $v)
		{
			$qs .= "&$k=" . encode_url($v);
		}
		$f = "html/search.php?1=1" . $qs;
		$content = file_get_contents($redirectURL . $f);
		
	break;	
	
	default:
		exit;
}

include("template-header.inc");
include("template.php");
include("template-footer.inc");


$_SESSION['crumb'] = $crumbs;
?>