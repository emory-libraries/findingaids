<?php
include_once("config.php");
include_once("lib/xmlDbConnection.class.php");

$connectionArray{"debug"} = false;

$xmldb = new xmlDbConnection($connectionArray);

$query = 'for $r in distinct-values(/ead/eadheader/eadid/@mainagencycode)
let $rep := (/ead[eadheader/eadid/@mainagencycode = $r]/archdesc/did/repository)[1] 
order by $rep 
return <repository agencycode="{$r}">{$rep/@*} {$rep/node()}</repository>';

/*$query = 'for $r in distinct-values(//archdesc/did/repository)
order by $r
return <repository>{$r}</repository>';*/

$xmldb->xquery($query);
$xsl_file 	= "stylesheets/search.xsl";
$xmldb->xslTransform($xsl_file);




?>

<div class='content' id='search'>


<h3>Search Collections</h3>

<form name="fa_query" action="search.php" method="get">
<table class="searchform" border="0">
<tr><th>Keyword</th><td class="input"><input type="text" size="40" name="keyword" value="<?= $kw?>"></td></tr>
<tr><th></th><td class="info">Searches entire text of finding aid</td></tr>


<tr><th>Creator</th><td class="input"><input type="text" size="40" name="creator" value="<?= $creator?>"></td></tr>
<tr><th></th><td class="info">Searches only for person, family, or organization that created or accumulated the collection [e.g., <b>Heaney, Seamus</b>]</td></tr>


<tr>
  <th>Filter by</th>
  <td class="input">
<select name="repository">
 <option selected value="all">--repository--</option>
<? $xmldb->printResult(); ?>
</select>
</td>
</tr>

<tr><td></td><td><input class="button" type="submit" value="Search"> <input class="button" type="reset" value="Reset"></td></tr>
</form>
</td>
</table>

<div class="searchtips">
<ul class ="searchtips"><b>Search tips:</b>
<li>You can enter words in more than one search box.</li>
<li>Asterisks may be used to do a truncated search. 
[e.g., enter <b>resign*</b> to match <b>resign</b>, <b>resigned</b>, and <b>resignation</b>.] </li>
<li>Capitalization is ignored.</li>
<!-- <li>Search for exact phrases using quotation marks [e.g., <b>"harlem renaissance"</b>] -->
</ul>
</div>



</div>
