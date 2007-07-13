<?
include("template-header.inc");

	displayBreadCrumbs($crumbs); 
	echo "<br />";
	
	if ($_REQUEST['kw'])
	{
		echo "<span class=\"keywords\">" . $_REQUEST['kw'] . "</span><br/>";
	}	
	

	echo $content;

include("template-footer.inc");
?>	