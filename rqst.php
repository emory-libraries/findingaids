<?php
include_once("common_functions.php");
include("marblcrumb.class.php");

$crumbs = new marblCrumb("Search", "rqst.php");
$crumbs->store();

html_head("Search - Finding Aids");
include("template-header.inc");

print $crumbs;

$kw = $_GET["keyword"];
$creator = $_GET["creator"];

?>


<div class='content' id='search'>

<table name="searchtable">
<tr><td>

<h2 class="alphaText">Search Collections</h2>

<form name="fa_query" action="search.php" method="get">
<table class="searchform" border="0">
<tr><th>Keyword</th><td class="input"><input type="text" size="40" name="keyword" value="<?php print $kw ?>"></td></tr>
<tr><th></th><td class="info">Searches entire text of finding aid</td></tr>


<tr><th>Creator</th><td class="input"><input type="text" size="40" name="creator" value="<?php print $creator ?>"></td></tr>
<tr><th></th><td class="info">Searches only for person, family, or organization that created or accumulated the collection [e.g., <b>Heaney, Seamus</b> or <b>Georgia Woman's Christian Temperance Union</b>]</td></tr>


<tr><td></td><td><input type="submit" value="Search"> <input type="reset" value="Reset"></td></tr>
</table>
</form>

</td>

<td class="searchtips" valign="top">
<ul class ="searchtips"><b>Search tips:</b>
<li>You can enter words in more than one search box.</li>
<li>Asterisks may be used to do a truncated search. 
[e.g., enter <b>resign*</b> to match <b>resign</b>, <b>resigned</b>, and <b>resignation</b>.] </li>
<li>Capitalization is ignored.</li>
<!-- <li>Search for exact phrases using quotation marks [e.g., <b>"harlem renaissance"</b>] -->
</ul>
</td>


</div>

<?php
include("template-footer.inc");
?>