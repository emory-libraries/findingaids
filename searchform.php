<?php
include_once("config.php");
include_once("lib/xmlDbConnection.class.php");

//php ajax/scriptaculous
include("projax/projax.php");

$connectionArray{"debug"} = false;

$xmldb = new xmlDbConnection($connectionArray);

/* organize by exist collection structure */
$query = 'for $r in ("' . implode('", "', $collections) . '")  
let $coll := concat("/db/FindingAids/", $r) 
let $code := distinct-values(collection($coll)//ead[' . $irishfilter . ']/eadheader/eadid/@mainagencycode) 
let $rep := (collection($coll)/ead/archdesc/did/repository)[1] 
order by $rep  
return <repository collection="{if ($r = \'emory/irish\') then \'emory\' else $r}" agencycode="{$code}">
	{$rep/@*}
	{$rep/node()}
</repository>';

/*$query = 'for $r in distinct-values(//archdesc/did/repository)
order by $r
return <repository>{$r}</repository>';*/

$xmldb->xquery($query);
$xsl_file 	= "stylesheets/search.xsl";
$xmldb->xslTransform($xsl_file);


$script = new Scriptaculous();


?>

<div class='content' id='search'>


<h3>Search Collections</h3>

<form name="fa_query" action="search.php" method="get">
<table class="searchform" border="0">
<tr><th>Keyword</th><td class="input"><input type="text" size="40" name="keyword" value="<?= $kw?>"></td></tr>
<tr><th></th><td class="info">Searches full text of all finding aids.</td></tr>


<tr><th>Creator</th>
<td class="input">
  <?
$ajaxopts = array("url" => "creatorlist.php", "indicator" => "loading", "select" => "value");
$inputopts = array("size" => "40", "value" => $creator, "autocomplete" => "off");
//print $script->auto_complete_field('creator', $opts);
print $script->text_field_with_auto_complete('creator', $inputopts, $ajaxopts);

?>

<!-- <input type="text" size="40" id="creator" name="creator" value="<?= $creator?>" autocomplete="off"> -->
<span id="loading" style="display:none;">Loading...</span>
<!-- <div id="creator_auto_complete" class="autocomplete"></div> -->
  </td></tr>

<tr><th></th><td class="info">Searches only for person, family, or organization that created or accumulated the collection [e.g., <b>Heaney, Seamus</b>]</td></tr>



<tr>
<th class="label">Filter by:</th>
</tr>

<tr>
  <th>Repository</th>
  <td class="input">
<select name="repository">
 <option selected value="all">--Search All--</option>
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
<li>You can enter words in both the keyword and creator search boxes
[e.g., keyword = <b>confetti</b> and creator = <b>carson, ciaran</b>].</li>
<li>Use <b>Filter by Repository</b> to limit your search to finding aids from a single instution
[e.g., keyword = <b>spreading</b>, creator = <b>Abbey</b>, Repository = <b>University of Delaware</b> ]</li>
<li>Asterisks may be used to do a truncated search. 
[e.g., enter <b>resign*</b> to match <b>resign</b>, <b>resigned</b>, and <b>resignation</b>.] </li>
<li>Capitalization is ignored.</li>
<!-- <li>Search for exact phrases using quotation marks [e.g., <b>"harlem renaissance"</b>] -->
</ul>
</div>



</div>
