<? 
	displayBreadCrumbs($crumbs); 
	echo "<br />";
	
	if ($_REQUEST['kw'])
	{
		echo "<span class=\"keywords\">" . $_REQUEST['kw'] . "</span><br/>";
	}	
	
	include("html/MARBL-bar.inc");

	echo $content;
?>	