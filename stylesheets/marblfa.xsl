<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
	xmlns:exist="http://exist.sourceforge.net/NS/exist"
	xmlns:ino="http://namespaces.softwareag.com/tamino/response2"
	xmlns:xq="http://metalab.unc.edu/xq/"
	xmlns:cti="http://cti.library.emory.edu/"
	version="1.0">
  <!--  <xsl:import href="ino.xsl"/>  -->
  <xsl:import href="toc.xsl"/> 
  <xsl:import href="summary.xsl"/> 
  <!--<xsl:import href="summary2.xsl"/> -->
  <!--  <xsl:import href="headingFooting.xsl"/> -->
  <!--  <xsl:strip-space elements="*"/>-->
  
  <xsl:param name="mode"/>
  
  <!-- any parameters to be added to urls within the site (e.g., for passing keywords) -->
  <xsl:param name="url_suffix"/>

  <!-- strings for translating case -->
  <xsl:variable name="lowercase" select="'abcdefghijklmnopqrstuvwxyz'"/>
  <xsl:variable name="uppercase" select="'ABCDEFGHIJKLMNOPQRSTUVWXYZ'"/>

  
<!-- <xsl:param name="content" ></xsl:param>   -->
  <!-- Creates the body of the finding aid.-->
  <xsl:template match="/">
    <xsl:choose>
      <xsl:when test="//ino:message/@ino:returnvalue &gt; 0">
        <xsl:element name="h1">Database Error</xsl:element>
        <xsl:apply-templates select="//ino:message"/>
        <xsl:element name="strong">Please contact <a href="mailto:jleon@emory.edu">Julia Leon</a></xsl:element>
      </xsl:when>
      
      <xsl:otherwise>	
        <div id="toc">	
        <h1>Table of Contents</h1>
        <hr/>
        <xsl:apply-templates select="//toc/ead/archdesc" mode="toc"/>
      </div>
      
      <div id="content"><!--start content-->
        <xsl:apply-templates select="//results/ead/eadheader/filedesc/titlestmt"/>
        <xsl:apply-templates select="//results/ead/*"/>		
      </div>
      
    </xsl:otherwise>
  </xsl:choose>

	
	<xsl:apply-templates select="//footing" mode="style"/>

</xsl:template>

<xsl:template match="frontmatter"></xsl:template>

<xsl:template match="dsc">
	<a>
	<xsl:attribute name="name"><xsl:value-of select="local-name()"/></xsl:attribute>
	</a>
	<xsl:choose>
	<!-- if at least 2 c levels exist, do a toc display -->
	<xsl:when test="c01/c02 or c01[@level='series']">
	<xsl:apply-templates mode="summary"/>
	</xsl:when>
	
	<!-- otherwise, display the full container list -->
	<!-- if there are no c02's then process all c01's with containers. Ignore the c01's that are headings -->
	<xsl:otherwise>
	<xsl:element name="h2">
	<xsl:apply-templates select="head"/>
	</xsl:element>
	<a><xsl:attribute name="name">series<xsl:number/>
	</xsl:attribute>
	</a>
	<table>
	<xsl:attribute name="border">0</xsl:attribute>
	<col width="7%" align="left" valign="top"/>
	<col width="7%" align="left" valign="top"/>
	<col width="86%"/>
	<thbody valign="top"/>
	<!-- process container c01's -->
	<xsl:apply-templates select="c01/did" mode="table"/>
	</table>
	</xsl:otherwise>
	</xsl:choose>
</xsl:template>


<xsl:template match="ead/eadheader">
	<xsl:element name="div">
          <xsl:attribute name="id">eadheader</xsl:attribute>
		<xsl:element name="h3"><xsl:apply-templates select="//publicationstmt/publisher" /></xsl:element>
		<xsl:element name="h4"><xsl:apply-templates select="//publicationstmt/address" /></xsl:element>	
	</xsl:element>
</xsl:template>

<xsl:template match="archdesc/did">
	<xsl:element name="h2">
	<a>
	<xsl:attribute name="name">descriptiveSummary</xsl:attribute>	
	Descriptive Summary
	</a>
	</xsl:element>

	<table>
	<col width="20%" align="left" valign="top"/>
	<col width="80%" align="left" valign="top"/>
	<thbody valign="top"/>
	<xsl:apply-templates mode="table"/>
	</table>

</xsl:template>

<xsl:template match="extent">
<xsl:text> </xsl:text><xsl:apply-templates/>
</xsl:template>

<xsl:template match="title[parent::unittitle]">
	<i><xsl:apply-templates/></i>
</xsl:template>

<xsl:template match="title">
	<i>
		<xsl:apply-templates/>
	</i>
</xsl:template>

<xsl:template match="addressline[not (local-name(../..)='titlepage')] | filedesc/publicationstmt//* | profiledesc//*">
	<xsl:apply-templates/><br/>
</xsl:template>
	
<xsl:template match="filedesc/publicationstmt" mode="table">
	<tr><td valign="top"/>
	<td>
	<xsl:apply-templates/>
	</td></tr>
</xsl:template>
	
	<!--<xsl:template match="archdesc/did/child::node()" mode="table">-->
<xsl:template match="archdesc/did/*" mode="table">
  <xsl:variable name="name"><xsl:value-of select="local-name()"/></xsl:variable>
	<tr><td valign="top">
	<xsl:choose>
	<xsl:when test="$name = 'unittitle'">Title:</xsl:when>
	<xsl:when test="$name = 'unitid'">Call Number:</xsl:when>
	<xsl:when test="$name = 'physdesc'">Extent:</xsl:when>
	<xsl:when test="$name = 'origination'">Creator:</xsl:when>
	<xsl:when test="$name = 'langmaterial'">Language:</xsl:when>
	<xsl:otherwise>
          <!-- use element name for label; capitalize the first letter -->
            <xsl:value-of select="concat(translate(substring($name,1,1),$lowercase, $uppercase),substring($name, 2, (string-length($name) - 1)))"/>: 
        </xsl:otherwise>
	</xsl:choose>
	</td>
	<td>
	<xsl:apply-templates/>
	</td></tr>
</xsl:template>

<!-- =============== unittitle ===============-->
<xsl:template match="did[parent::c01 | parent::c02 | parent::c03 | parent::c04 | parent::c04 | parent::c05 | parent::c06 | parent::c07 | parent::c08 | parent:: c09]/unittitle" priority="8">

<!-- toc
<xsl:apply-templates select="ancestor::c01" mode="toc"/>
-->
<xsl:apply-templates />
<xsl:text> </xsl:text><xsl:apply-templates select="../unitdate"/>
</xsl:template>

<xsl:template match="did[parent::c01 | parent::c02 | parent::c03 | parent::c04 | parent::c04 | parent::c05 | parent::c06 | parent::c07 | parent::c08 | parent:: c09]/unittitle[parent::did[not(container)]]" priority="7">
<xsl:if test="preceding-sibling::unitid">
<xsl:value-of select="normalize-space(',')"/><xsl:text> </xsl:text>
</xsl:if>
<xsl:apply-templates/>
</xsl:template>

<xsl:template match="did[parent::c01 | parent::c02 | parent::c03 | parent::c04 | parent::c04 | parent::c05 | parent::c06 | parent::c07 | parent::c08 | parent:: c09]/unittitle" priority="6">
<xsl:apply-templates/>
</xsl:template>

<!-- =============== unitdate ===============-->
<!-- put a comma before the unitdate if this is not a container or if it's part of the archdesc -->
<!-- 
2006.08.29 RSK
removed comma before unitdate at Susan's request
<xsl:template match="did[parent::c01 | parent::c02 | parent::c03 | parent::c04 | parent::c04 | parent::c05 | parent::c06 | parent::c07 | parent::c08 | parent:: c09]//unitdate[ancestor::did[1][not(container)]] | archdesc/did//unitdate" priority="7">
<xsl:if test="local-name(preceding-sibling::node()[1])='unitdate'">
<xsl:value-of select="normalize-space(',')"/><xsl:text> </xsl:text>
</xsl:if>
<xsl:text> </xsl:text>
<xsl:apply-templates/>
</xsl:template> -->

<xsl:template match="did[parent::c01 | parent::c02 | parent::c03 | parent::c04 | parent::c04 | parent::c05 | parent::c06 | parent::c07 | parent::c08 | parent:: c09]//unitdate" priority="6">
<xsl:text> </xsl:text>
<xsl:apply-templates/>
</xsl:template>

<xsl:template match="unitdate" priority="5">
<xsl:text> </xsl:text>
<xsl:apply-templates/>
</xsl:template>
<!-- ===============  ===============-->


<xsl:template match="subarea">
<xsl:value-of select="normalize-space(',')"/><xsl:text> </xsl:text>
<xsl:apply-templates/>
</xsl:template>

<xsl:template match="did[parent::c01 | parent::c02 | parent::c03 | parent::c04 | parent::c04 | parent::c05 | parent::c06 | parent::c07 | parent::c08 | parent:: c09]//physdesc">
<xsl:element name="h3">
<xsl:apply-templates/>
</xsl:element>
</xsl:template>

<!-- =========== unitid  =========== -->
<xsl:template match="did[parent::c01 | parent::c02 | parent::c03 | parent::c04 | parent::c04 | parent::c05 | parent::c06 | parent::c07 | parent::c08 | parent:: c09]/unitid" priority="8">

<xsl:apply-templates />

</xsl:template>
<!-- ===========   =========== -->

<xsl:template match="titlestmt">
  <div id="headingBlock">
    <xsl:element name="span">
      <xsl:attribute name="class">content_title</xsl:attribute>
      <xsl:apply-templates select="titleproper"/>
    </xsl:element>
    
    <xsl:element name="span">
      <xsl:attribute name="class">content_subtitle</xsl:attribute>
      <xsl:value-of select="subtitle"/>	
    </xsl:element>
  </div>
</xsl:template>
             
<xsl:template match="ead/archdesc">
	<div class="content">
	<xsl:apply-templates select="ead/eadheader"/>
	<xsl:apply-templates select="did" />
	<hr/>
	<xsl:element name="h2">
	<a>
	<xsl:attribute name="name">adminInfo</xsl:attribute>
	Administrative Information
	</a> 
	</xsl:element>
	<xsl:apply-templates select="acqinfo | accessrestrict | userestrict | prefercite | separatedmaterial"/>
	<hr/>
	<xsl:element name="h2">
	<a>
	<xsl:attribute name="name">collectionDesc</xsl:attribute>
	Collection Description
	</a>
	</xsl:element>
	<xsl:apply-templates select="bioghist | scopecontent | arrangement"/>
	<hr/>
        <xsl:apply-templates select="controlaccess"/>
	<hr/>
	<xsl:apply-templates select="dsc"/>
	</div>
</xsl:template>





<!-- The following templates format the display of various RENDER attributes.-->

<!-- This template converts a Ref element into an HTML anchor.-->

<!--This template rule formats a list element.-->
<xsl:template match="list">
<xsl:element name="ul">
<xsl:apply-templates select="item"/>
</xsl:element>
</xsl:template>

<xsl:template match="ead/archdesc/scopecontent/organization//item">
<xsl:element name="li">
<a><xsl:attribute name="href">#series<xsl:number/>
</xsl:attribute>
<xsl:apply-templates/>
</a>
</xsl:element>
</xsl:template>

<xsl:template match="item">
<xsl:element name="li">
<xsl:apply-templates/>
</xsl:element>
</xsl:template>


<!-- commented out 2006.06.27 by RSK
  I think these two templates are completely unnecessary, as they do the default action,  
  and may cause unexpected behavior elsewhere 
<xsl:template match="archdesc/*" priority="-1">
<xsl:apply-templates/>
</xsl:template>

<xsl:template match="*[not(text())]" priority="-2">
<xsl:apply-templates/>
</xsl:template>
 -->

<!-- repeating element, needs generative href attribute value -->
<xsl:template match="bioghist">
<xsl:element name="h3">
<a>
<xsl:attribute name="name"><xsl:value-of select="local-name(parent::node())"/>.<xsl:value-of select="position()"/></xsl:attribute>
<xsl:value-of select="head"/>
</a>
</xsl:element>
<xsl:apply-templates select="*[not(self::head)]"/>
</xsl:template>

<!--<xsl:template match="archdesc/*/head[not(ancestor::dsc)] | dsc/head">-->
<xsl:template match="archdesc/*/head[not(ancestor::dsc)]">
<xsl:element name="h3">
<a>
<xsl:attribute name="name"><xsl:value-of select="local-name(parent::node())"/></xsl:attribute>
<xsl:apply-templates/>
</a>
</xsl:element>
</xsl:template>

<xsl:template match="controlaccess">
  <xsl:apply-templates select="head"/>
  <p class="indent">
    <xsl:apply-templates select="*[not(self::head)]"/>
  </p>
</xsl:template>

<xsl:template match="ead/archdesc/controlaccess//controlaccess/head">
<h4>
<xsl:attribute name="class">indent</xsl:attribute>
<xsl:apply-templates/>
</h4>
</xsl:template>

<xsl:template match="controlaccess[controlaccess]/head">
  <h2>
    <a name="searchTerms">
      <xsl:apply-templates/>
    </a>
  </h2>
</xsl:template>


<xsl:template match="ead/archdesc/bioghist/bioghist">
<h2>
<xsl:apply-templates select="head"/>
</h2>
<xsl:for-each select="p">
<p style="margin-left: 30pt">
<xsl:apply-templates />
</p>
</xsl:for-each>
</xsl:template>

<!-- This formats an organization list embedded in a scope content statement.-->
<xsl:template match="ead/archdesc/scopecontent/organization">
<xsl:apply-templates select="p"/>
<xsl:apply-templates select="list"/>
</xsl:template>

<xsl:template match="ead/archdesc/dsc/p" >
<p>
<xsl:attribute name="class">indent</xsl:attribute>
<i>
<xsl:apply-templates/>
</i>
</p>
</xsl:template>

<xsl:template match="p | bibref">
<p>
<xsl:attribute name="class">indent</xsl:attribute>
<xsl:apply-templates/>
</p>
</xsl:template>

<xsl:template match="text()">
  <xsl:value-of select="."/>
</xsl:template> 

<!-- used for development, to see that all elements are considered -->
<xsl:template match="ead/eadheader/filedesc"
  priority="-1">
<xsl:apply-templates/>
</xsl:template>

<xsl:template match="subject |corpname[not(parent::origination)] | controlaccess/persname | controlaccess/famname | controlaccess/title| genreform | geogname | occupation">
<xsl:element name="span">
<xsl:attribute name="class">indent</xsl:attribute>
<xsl:apply-templates/>
</xsl:element>
<br/>
</xsl:template>

<!-- in case of multiple languages, spaces are getting lost around the "and"; put spaces back in here -->
<xsl:template match="langmaterial/language">
  <xsl:if test="preceding-sibling::language">
    <xsl:text> </xsl:text>
  </xsl:if>
  <xsl:apply-templates/>
  <xsl:if test="following-sibling::language">
    <xsl:text> </xsl:text>
  </xsl:if>
</xsl:template>


<!-- ================ setting up the container list tables ========= -->
<!-- Processing the highest c-level in return set -->
<xsl:template match="c01|c02|c03">

<!--
<a>
	<xsl:attribute name="name">series<xsl:number/></xsl:attribute>
</a>
-->
<!-- process only at this container level, not sub-containers -->
<xsl:element name="h2">
<xsl:apply-templates select="did/unitid"/>
<br/>
<xsl:text> </xsl:text>
<xsl:apply-templates select="did/unittitle"/>
<xsl:text> </xsl:text>
<xsl:apply-templates select="did/unitdate"/>
<br/>
<xsl:value-of select="did/physdesc"/>
</xsl:element>


<xsl:apply-templates select="scopecontent"/>
<xsl:apply-templates select="bibliography"/>
<xsl:apply-templates select="bioghist"/>
<xsl:apply-templates select="arrangement"/>


<table>
<col width="7%" align="left" valign="top"/>
<col width="7%" align="left" valign="top"/>
<col width="86%"/>
<thbody valign="top"/>

<!-- process sub-container -->
<xsl:apply-templates select="c02/did | c03/did | c04/did | c05/did | c06/did | c07/did | c08/did | c08/did | c09/did" mode="table"/>

</table>
</xsl:template>

<!-- ================ processing the c0n/did's   ========= -->
<!-- Shows the box and folder numbers containers  -->
<xsl:template match="did[parent::c01 | parent::c02 | parent::c03 | parent::c04 | parent::c04 | parent::c05 | parent::c06 | parent::c07 | parent::c08 | parent:: c09][container[@type='box']]" mode="table"> 


<!-- only show box/folder once for the whole page -->
<xsl:if test="count(../preceding-sibling::node()/did) = 0">
  <tr><td valign="top">
  <p/><b>Box</b></td><td><p/><b>Folder</b></td></tr> 
</xsl:if>

<tr>
<td valign="top">
<xsl:apply-templates select="container[@type='box']" mode="table"/>
 </td>
<td valign="top">
<xsl:apply-templates select="container[@type='folder']" mode="table"/>
 </td>
<td valign="top">
<xsl:apply-templates select="unitid"/>
<xsl:text> </xsl:text>
<xsl:apply-templates select="unittitle"/>
<xsl:apply-templates select="physdesc"/>
<xsl:apply-templates select="abstract"/>
<xsl:apply-templates select="note"/>
</td>
</tr>
</xsl:template>

<!-- container of volumes -->
<xsl:template match="did[parent::c01 | parent::c02 | parent::c03 | parent::c04 | parent::c04 | parent::c05 | parent::c06 | parent::c07 | parent::c08 | parent:: c09][container[@type='volume']]" mode="table">
<!-- if new volume number, print volume,folder header -->
<xsl:if test="not(../preceding-sibling::node()[1]/did/container[@type='volume']=container[@type='volume'])"> 
<tr><td valign="top">
<b>Volume</b></td><td><b> </b></td></tr>
</xsl:if>

<tr>
<td valign="top">
<xsl:apply-templates select="container[@type='volume']" mode="table"/>
 </td>
<td valign="top">
 </td>
<td valign="top">
<xsl:apply-templates select="unitid"/>
<xsl:text> </xsl:text>
<xsl:apply-templates select="unittitle"/>
<xsl:apply-templates select="physdesc"/>
<xsl:apply-templates select="abstract"/>
<xsl:apply-templates select="note"/>
</td>
</tr>
</xsl:template>

<!-- scope and content and arrangement -->
<xsl:template match="scopecontent[parent::c01] | arrangement[parent::c01]">
	<!--<xsl:template match="scopecontent">-->
	<!--<h3><xsl:value-of select="head"/></h3>-->
	<xsl:apply-templates />
</xsl:template>

<xsl:template match="scopecontent[parent::c01|parent::c02]/head | arrangement[parent::c01|parent::c02]/head">
	<h3><xsl:value-of select="."/></h3>
</xsl:template>

<!-- c levels without containers, used as subseries headers -->
<xsl:template match="did[parent::c01 | parent::c02 | parent::c03 | parent::c04 | parent::c04 | parent::c05 | parent::c06 | parent::c07 | parent::c08 | parent:: c09][not(container)]" mode="table">
<tr>
<td colspan="3">

<!-- don't list folder contents -->
<xsl:choose>

<!-- Print link if only 1 more c levels exist below this -->
<xsl:when test="parent::node()[c02 or c03 or c04 or c05 or c06 or c07 or c08]">
  <p>
<xsl:element name="h4">
<a>
<xsl:attribute name="name"><xsl:apply-templates   select="ancestor::node()[self::c01 | self::c02| self::c03 | self::c04 | self::c05 | self::c06 | self::c07 | self::c08| self::c09]" mode="c-level-index"/>
</xsl:attribute>
<xsl:attribute name="href">content.php?el=<xsl:value-of select="local-name(parent::node())"/>&amp;id=<xsl:value-of select="parent::c01/@id"/><xsl:value-of select="parent::c02/@id"/><xsl:value-of select="parent::c03/@id"/><xsl:value-of select="parent::c04/@id"/><xsl:value-of select="parent::c05/@id"/><xsl:value-of select="parent::c06/@id"/><xsl:value-of select="parent::c07/@id"/><xsl:value-of select="parent::c08/@id"/><xsl:value-of select="parent::c09/@id"/><xsl:value-of select="$url_suffix"/></xsl:attribute>
<xsl:apply-templates select="unitid"/>:
<xsl:text> </xsl:text>
<xsl:apply-templates select="unittitle"/>
<xsl:text> </xsl:text>
<xsl:apply-templates select="unitdate"/>
</a> 

<!-- count & display # of matches in this section -->
  <xsl:variable name="hits">	
  <!-- not sure why, but this path seems to give a more accurate number... -->
    <xsl:value-of select="count(..//exist:match)"/>
  </xsl:variable>

  <xsl:if test="$hits > 0">
    <span class="hits">
      <xsl:value-of select="$hits"/> hit<xsl:if test="$hits > 1">s</xsl:if>
    </span>
  </xsl:if>

</xsl:element>
</p>

</xsl:when>

<xsl:otherwise>
<!--  a file without containers (used as a heading to subsequent sibling c-levels? -->
<p/>
<h4><xsl:apply-templates/></h4>
</xsl:otherwise>
</xsl:choose>
</td>
</tr>
</xsl:template>
<!-- ====================================================== -->

<xsl:template match="cti:h1">
  <h1>
    <xsl:attribute name="class">
      <xsl:apply-templates select="@class"/>
    </xsl:attribute>
    <xsl:apply-templates/>
  </h1>
</xsl:template>

<!-- now that we are retrieving at the c01 level, the relative position of c01 will always be '1' -->
<xsl:template match="c01" mode="c-level-index">
<xsl:value-of select="local-name()"/>.<xsl:number value="0+1"/>:</xsl:template>
  
<xsl:template match=" c02 | c03 | c04 | c05 | c06 | c07 | c08 | c09" mode="c-level-index">
<xsl:value-of select="local-name()"/>.<xsl:number value="count(preceding-sibling::*[self::c01 | self::c02| self::c03 | self::c04 | self::c05 | self::c06 | self::c07 | self::c08| self::c09 ])+1"/>:</xsl:template>


<xsl:template match="exist:match">
  <xsl:variable name="txt"><xsl:value-of select="preceding::text()[0]"/></xsl:variable>
  <!--  DEBUG: preceding text is :<xsl:value-of select="$txt"/>:<br/>  -->
  <!-- for some reason, the single space between two matching terms is getting lost; put it back in here. -->
  <xsl:if test="preceding-sibling::exist:match and ($txt = '')">
    <xsl:text> </xsl:text>
  </xsl:if> 

  <span class="match"><xsl:apply-templates/></span>
</xsl:template>


<!-- tamino highlighting -->
<!-- mark text after a MATCH + n processing instruction as a match to highlight -->
<xsl:template match="text()[preceding-sibling::processing-instruction('MATCH')]">
  <xsl:variable name="pi"><xsl:value-of select="preceding-sibling::processing-instruction('MATCH')[1]"/></xsl:variable>
  <xsl:choose>
    <xsl:when test="starts-with($pi, '+')">
      <span class="match">
        <xsl:value-of select="."/> 
      </span>
    </xsl:when>
    <xsl:otherwise> <!-- this is the text following the match -->
      <xsl:value-of select="."/>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<!-- Match the processing instruction and perform action -->
<xsl:template match="processing-instruction('MATCH')">
	<xsl:if test="preceding::processing-instruction('MATCH') or following::processing-instruction('MATCH')">
	  	<xsl:variable name="n"><xsl:value-of select="count(preceding::processing-instruction('MATCH'))"/></xsl:variable>
		  <a>
		    <xsl:attribute name="name">m<xsl:value-of select="$n"/></xsl:attribute>
		    <xsl:choose>
		      <xsl:when test="starts-with(., '+') and preceding::processing-instruction('MATCH')">
		        <xsl:attribute name="href">#m<xsl:value-of select="($n - 1)"/></xsl:attribute>
					<img src="html/images/previous-match.gif" border="0"/> 
		      </xsl:when>
		      <xsl:when test="starts-with(., '-') and following::processing-instruction('MATCH')">
		        <xsl:attribute name="href">#m<xsl:value-of select="($n + 1)"/></xsl:attribute>
		 			<img src="html/images/next-match.gif" border="0"/> 
		      </xsl:when>		      
		    </xsl:choose>
		  </a>
	</xsl:if>
</xsl:template>

<xsl:template match="hits">
 <!-- don't display anything if there are zero hits -->
  <xsl:if test=". != 0">
    <span class="hits">
      <xsl:apply-templates/> hit<xsl:if test=". > 1">s</xsl:if>
    </span>
  </xsl:if>
</xsl:template>


</xsl:stylesheet>
