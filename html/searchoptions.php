<div class='content' id='search'>

<table name="searchtable">
<tr><td>

<h2>Advanced Search</h2>

<form name="fa_query" action="search" method="post">
<table class="searchform" border="0">
<tr><th>Keyword</th><td class="input"><input type="text" size="40" name="keyword" value="<?php print $kw ?>"></td></tr>
<!--<tr><th>Title</th><td class="input"><input type="text" size="40" name="title" value="<?php print $title ?>"></td></tr>-->
<tr><th>Creator</th><td class="input"><input type="text" size="40" name="author" value="<?php print $author ?>"></td></tr>
<!--
<tr><th>Sermon Date</th><td class="input"><input type="text" size="40" name="date" value="<?php print $date ?>"></td></tr>
<tr><th>Place of Publication</th><td class="input"><input type="text" size="40" name="place" value="<?php print $place ?>"></td></tr>
-->
<tr><td></td><td><input type="submit" value="Submit"> <input type="reset" value="Reset"></td></tr>
</table>
</form>


<h2>Specialized Search</h2>
<form name="advancedquery" action="search" method="post">
<table class="searchform" border="0">
<tr><th>Enter word or phrase:</th><td class="input"><input type="text" size="40" name="keyword"></td></tr>
<tr><th>Type of search:</th><td>
<input type="radio" name="mode" value="exact" CHECKED>Exact Phrase
<input type="radio" name="mode" value="phonetic">Phonetic
<!-- This requires a defined dictionary which we do not have yet<input type="radio" name="mode" value="synonym">Synonym</td>-->
</tr>
<tr><td></td><td><input type="submit" value="Submit"><input type="reset" value="Reset"></td></tr> 
</table>
</form>
</td>

<td class="searchtips" valign="top">
<ul class ="searchtips"><b>Search tips:</b>
<li>Search terms are matched against <i>whole words</i></li>
<li>Multiple words are allowed, and will return documents containing all terms anywhere in the text.</li>
<li>Asterisks may be used when using a part of a word or words. <br>
For example, enter <b>resign*</b> to match <b>resign</b>, <b>resigned</b>, and
<b>resignation</b>. </li>
<li> Use several categories to narrow your search. For example, keyword and<br>creator to match a particular finding aid.</li>
</ul>
</td>


</div>
