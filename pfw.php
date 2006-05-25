<?
$url_qs = key($_REQUEST);
//echo "url_qs=$url_qs<hr>";

//$pattern = '/(.*)(-)(.*)*/';
//preg_match($pattern, $url_qs, $matches) > 0;
//list($devnull, $cmd, $devnull, $id) = $matches;
//echo "<pre>"; print_r($matches); echo "</pre>";


$cmd = split('-', $url_qs);
//echo "<pre>"; print_r($cmd); echo "</pre>";
//exit;


switch ($cmd[0])
{
	case 'banner':
		$f = "html/". $cmd[1] .".html";
	break;
	
	case 'tamino': 
		$f = "html/result.php?".end($cmd);		
		//$f = "marbl.php";
	break;
	
	case 'browse':
		$f = "html/browse.php?l=".$cmd[2];
	break;
	
	case 'section':		
		switch ($cmd[1])
		{
			case 'toc':
				$f = "html/toc.php?id=".end($cmd);
			break;
			
			case 'content':			
				$e = (count($cmd) > 3) ? $cmd[2] : '';
				$f = "html/content.php?element=$e&id=".end($cmd);	
			break;
		}
	break;
	
	default:
		echo "<pre>"; print_r($matches); echo "</pre><hr>";
		echo "<pre>"; print_r($_REQUEST); echo "</pre><hr>";
		$f = $url_qs;
		exit;
}
//echo ("http://biliku.library.emory.edu/jbwhite/projects/marblfa-php/" . $f);
readfile("http://biliku.library.emory.edu/jbwhite/projects/marblfa-php/" . $f);
?>