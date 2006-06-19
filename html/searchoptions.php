<div class='content' id='search'>

<table name="searchtable">
<tr><td>

<h2>Advanced Search</h2>

<form name="fa_query" action="search" method="post">
<table class="searchform" border="0">
<tr><th>Keyword</th><td class="input"><input type="text" size="40" name="keyword" value="<?php print $kw ?>"></td></tr>
<tr><th></th><td><span class="support_text">Searches entire text of finding aid</span></td></tr>


<tr><th>Creator</th><td class="input"><input type="text" size="40" name="author" value="<?php print $author ?>"></td></tr>
<tr><th></th><td><span class="support_text">Searches only for person, family, or organization that created or accumulated the collection</span></td></tr>
<tr><th></th><td><span class="support_text">[e.g.<b>Heaney, Seamus</b> or <b>Georgia Woman's Christian Temperance Union</b></span></td></tr>


<tr><td></td><td><input type="submit" value="Search"> <input type="reset" value="Reset"></td></tr>
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
<tr><td></td><td><input type="submit" value="Search"><input type="reset" value="Reset"></td></tr> 
</table>
</form>
</td>

<td class="searchtips" valign="top">
<ul class ="searchtips"><b>Search tips:</b>
<li>You can words in more than one search box.</li>
<li>Asterisks may be used to do a truncated search.<br>
For example, enter <b>resign*</b> to match <b>resign</b>, <b>resigned</b>, and <b>resignation</b>. </li>
<li>Capitalization is ignored.</li>
</ul>
</td>


</div>
