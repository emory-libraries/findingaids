<?
include("web/html/template-header.inc");

	displayBreadCrumbs($crumbs); 
	echo "<br />";
	
	if ($_REQUEST['kw'])
	{
		echo "<span class=\"keywords\">" . $_REQUEST['kw'] . "</span><br/>";
	}	
	

	echo $content;

include("web/html/template-footer.inc");
?>	