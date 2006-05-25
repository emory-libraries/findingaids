<?xml version="1.0" encoding="ISO-8859-1"?> 

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:html="http://www.w3.org/TR/REC-html40" version="1.0"
   	xmlns:xalan="http://xml.apache.org/xalan"
	xmlns:ino="http://namespaces.softwareag.com/tamino/response2" 
	xmlns:xql="http://metalab.unc.edu/xql/" 
        xmlns:tf="http://namespaces.softwareag.com/tamino/TaminoFunction" 
        xmlns:js="javascript:code"
  	extension-element-prefixes="js">


<xsl:variable name="query"><xsl:value-of select="ino:response/xql:query"/></xsl:variable>
<xsl:variable
name="base_url">http://tamino.library.emory.edu/passthru/servlet/transform/tamino/BECKCTR/ILN</xsl:variable>
<xsl:variable name="image_url">http://chaucer.library.emory.edu/iln/images/</xsl:variable>

<!-- define variables for all xsl files -->
<xsl:variable name="xsl_browse">ilnbrowse.xsl</xsl:variable>
<xsl:variable name="xsl_search">ilnsearch.xsl</xsl:variable>
<xsl:variable name="xsl_contents">ilncontents.xsl</xsl:variable>
<xsl:variable name="xsl_imgview">imgview.xsl</xsl:variable>
<xsl:variable name="xslurl">&amp;_xslsrc=xsl:stylesheet/</xsl:variable>


<!-- javascript to colorize a search string -->
<!-- multiple terms should be passed in as match1|match2|match3 -->
<xalan:component prefix="js" functions="highlight">
    <xalan:script lang="javascript">
                                                                                        
function highlight (string, match) {
 var debug = 0;	// set to 1 for testing
 var fixre = new RegExp("\\*", "gi");
 match = match.replace(fixre, "\\w\*");
                                                                                   
 if (debug) { document.write("regexp match is " + match + "<br/>"); }
                                                                                   
 var pattern = new RegExp("(\\b"+match+"\\b)", "gi")
 if (debug) { document.write("pattern is " + pattern + "<br/>"); }
 var color = string.replace( pattern,
        "<font color='red'><b>$1</b></font>");
                                                                                   
 document.writeln(color);
 document.write("<p/>");
                                                                                   
}
</xalan:script>
</xalan:component>




<!-- set processing instructions -->
<xsl:template name="proc_instr">
  <xsl:processing-instruction name="cocoon-format">
    type="text/html"
  </xsl:processing-instruction>
</xsl:template>

<!-- define html head -->
<xsl:template name="html_head">
  <xsl:element name="head">
  <!-- FIXME: how to vary 1st part of title according to mode? -->
  <xsl:element name="title">
  <xsl:value-of select="$mode_name" /> - The Civil War in America from The Illustrated London News
  </xsl:element> <!-- title -->
  <xsl:element name="script">
    <xsl:attribute name="language">Javascript</xsl:attribute>
    <xsl:attribute name="src">http://chaucer.library.emory.edu/iln/image_viewer/launchViewer.js</xsl:attribute>
  </xsl:element><!-- script -->
  <xsl:element name="script">
    <xsl:attribute name="language">Javascript</xsl:attribute>
    <xsl:attribute name="src">http://chaucer.library.emory.edu/iln/iln_functions.js</xsl:attribute>
  </xsl:element> <!-- script -->
  <script language="javascript">
   getBrowserCSS();
  </script>
  <!-- if not running javascript, get default css -->
  <noscript>
    <link rel="stylesheet" type="text/css" href="http://chaucer.library.emory.edu/iln/iln.css"/>
  </noscript>

  </xsl:element> <!-- head -->
</xsl:template>

<xsl:template name="html_title">
     <xsl:element name="h2"><xsl:value-of select="$mode_name"
/></xsl:element>
<!-- warn users, in case javascript is turned off --> 
  <xsl:element name="noscript">
  <i>Note: Some features of this site require Javascript</i>
  <!-- don't display javascript viewer version of figures -->
      <style type="text/css">
        img.javascript { display: none }
      </style>
  </xsl:element>

</xsl:template>


<!-- display figure & link to image-viewer -->
<xsl:template match="figure">
    <xsl:element name="table">
      <xsl:element name="tr">
        <xsl:element name="td">
      <xsl:element name="a">
  <xsl:attribute name="href">javascript:launchViewer('<xsl:value-of
      select="concat($base_url,'?_xql=TEI.2//figure[@entity=')"/>\'<xsl:value-of select="./@entity"/>\'<xsl:value-of select="concat(']', $xslurl,
	   $xsl_imgview)"/>')</xsl:attribute>
<xsl:element name="img">
  <xsl:attribute name="class">javascript</xsl:attribute>
  <xsl:attribute name="src"><xsl:value-of select="concat($image_url, 'ILN', @entity, '.gif')"/></xsl:attribute>
  <xsl:attribute name="alt">view image</xsl:attribute>
  </xsl:element> <!-- end img -->
  </xsl:element> <!-- end a --> 

<!-- non javascript version of image & link -->
<!-- note: if neither javascript nor css works, there will be two
   copies of image (but other things will probably be broken also) -->
  <noscript>
      <xsl:element name="a">
  <xsl:attribute name="href"><xsl:value-of select="concat($image_url, 'ILN', @entity, '.jpg')"/></xsl:attribute>
  <xsl:element name="img">
  <xsl:attribute name="src"><xsl:value-of select="concat($image_url, 'ILN', @entity, '.gif')"/></xsl:attribute>
  <xsl:attribute name="alt">view image</xsl:attribute>
  </xsl:element> <!-- end img -->
  </xsl:element> <!-- end a --> 
 </noscript> 

  </xsl:element> <!-- end td -->

   <xsl:element name="td">
     <xsl:element name="p">
      <xsl:attribute name="class">caption</xsl:attribute>
      <xsl:value-of select="head"/>
     </xsl:element> <!-- p -->

  </xsl:element> <!-- end td -->
  </xsl:element> <!-- end tr --> 
  </xsl:element>  <!-- end table -->
</xsl:template>


<!-- print out div titles in table of contents style -->
<xsl:template match="div2"> 

 <xsl:element name="p">
  <xsl:element name="a">
   <xsl:attribute name="href"><xsl:value-of
      select="$base_url"/>?_xql(<xsl:value-of
select="position()"/>,1)=<xsl:value-of select="concat($query, $xslurl,
	$xsl_browse)"/>&amp;xslt_xql=<xsl:value-of
select="$query"/>&amp;xslt_rmode=<xsl:value-of
select="$curxsl"/><xsl:if test="$max !=
0">&amp;xslt_range=<xsl:value-of select="$start"/>,<xsl:value-of select="$max"/></xsl:if>
  </xsl:attribute>  
  <!-- if no title, label as untitled -->
  <xsl:if test="head = ''">Untitled</xsl:if>
  <xsl:apply-templates select="head"/>
</xsl:element> <!-- end a -->
 <xsl:element name="font">
 <xsl:attribute name="size">-1</xsl:attribute>
  - <xsl:value-of select="./@type"/>
  - <xsl:value-of select="bibl/date" /> 
  <xsl:if test="bibl/extent">
      - (<xsl:value-of select="bibl/extent" />)
  </xsl:if>
  </xsl:element> <!-- end font -->
</xsl:element> <!-- end a -->

</xsl:template>



<!-- default template that calls highlight if match is defined -->
<xsl:template match="@*|node()" name="default">
    <xsl:choose>
      <xsl:when test="function-available('js:highlight')">
<!-- TESTING: javascript function available!  using js:highlight -->
          <xsl:value-of select="js:highlight(normalize-space(.), $match)"/>
      </xsl:when>
      <xsl:when test="contains($match, '|')">
       <xsl:variable name="color-string"> 
 	<xsl:call-template name="highlight">
 	   <xsl:with-param name="string" select="normalize-space(.)"/>
  	   <xsl:with-param name="match"
		select="substring-before($match, '|')"/>
	</xsl:call-template>
       </xsl:variable>
 	<xsl:call-template name="highlight">
 	   <xsl:with-param name="string"><xsl:copy-of
		select="$color-string"/></xsl:with-param>
  	   <xsl:with-param name="match"
		select="substring-after($match, '|')"/>
	</xsl:call-template>
      </xsl:when>  
      <xsl:when test="$match != 0"> 
 	<xsl:call-template name="highlight">
 	   <xsl:with-param name="string" select="normalize-space(.)"/>
  	   <xsl:with-param name="match" select="$match"/>
	</xsl:call-template>  
        <!--        <xsl:value-of select="tf:highlight(., $match)"/> -->
      </xsl:when>

      <xsl:otherwise>
         <xsl:value-of select="normalize-space(.)"/>
      </xsl:otherwise>
   </xsl:choose>
</xsl:template>


<!-- recursive template to highlight search term -->
<xsl:template name="highlight">
  <xsl:param name="string"/> 
  <xsl:param name="match" select="string()" /> 


<xsl:variable name="lowercase">abcdefghijklmnopqrstuvwxyz</xsl:variable>
<xsl:variable name="uppercase">ABCDEFGHIJKLMNOPQRSTUVWXYZ</xsl:variable>

  <!-- all upper case -->
  <xsl:variable name="ucmatch"><xsl:value-of select="translate($match,
	 $uppercase, $lowercase)"/></xsl:variable>
  <!-- all lower case -->
  <xsl:variable name="lcmatch"><xsl:value-of select="translate($match,
	 $lowercase, $uppercase)"/></xsl:variable>
  <!-- first letter capitalized -->
  <xsl:variable name="Match"><xsl:value-of
	select="translate(substring($match, 1, 1), $lowercase,
	$uppercase)"/><xsl:value-of select="translate(substring($match, 2),
	$uppercase, $lowercase)"/></xsl:variable>
<!-- FIXME: after a space, must capitalize next word also... -->

 <xsl:choose>
   <xsl:when test="contains($string, $match)">
      <xsl:call-template name="colorize">
	<xsl:with-param name="string" select="$string"/>
	<xsl:with-param name="match" select="$match"/>
      </xsl:call-template>
   </xsl:when>
   <xsl:when test="contains($string, $ucmatch)">
      <xsl:call-template name="colorize">
	<xsl:with-param name="string" select="$string"/>
	<xsl:with-param name="match" select="$ucmatch"/>
      </xsl:call-template>
   </xsl:when>
   <xsl:when test="contains($string, $lcmatch)">
      <xsl:call-template name="colorize">
	<xsl:with-param name="string" select="$string"/>
	<xsl:with-param name="match" select="$lcmatch"/>
      </xsl:call-template>
   </xsl:when>
   <xsl:when test="contains($string, $Match)">
      <xsl:call-template name="colorize">
	<xsl:with-param name="string" select="$string"/>
	<xsl:with-param name="match" select="$Match"/>
      </xsl:call-template>
   </xsl:when>
   <xsl:otherwise>
      <!-- print out the whole string as is -->
      <xsl:value-of select="$string"/>
   </xsl:otherwise>
 </xsl:choose>

  <!-- variable must be declared outside of condition -->
  <xsl:variable name="aftermatch">
    <xsl:choose>
    <xsl:when test="contains($string, $match)">  
       <xsl:value-of select="substring-after($string, $match)"/>
    </xsl:when>
    <xsl:when test="contains($string, $ucmatch)">  
       <xsl:value-of select="substring-after($string, $ucmatch)"/>
    </xsl:when>
    <xsl:when test="contains($string, $lcmatch)">  
       <xsl:value-of select="substring-after($string, $lcmatch)"/>
    </xsl:when>
    <xsl:when test="contains($string, $Match)">  
       <xsl:value-of select="substring-after($string, $Match)"/>
    </xsl:when>
    </xsl:choose>
  </xsl:variable>
   

  <xsl:choose>
  <!-- recurse if there is another instance of the match string -->
  <xsl:when test="contains($aftermatch, $match)">
     <xsl:call-template name="highlight">
        <xsl:with-param name="string" select="$aftermatch" />
	<xsl:with-param name="match" select="$match"/>
      </xsl:call-template>
  </xsl:when>
  <xsl:when test="contains($aftermatch, $ucmatch)">
     <xsl:call-template name="highlight">
        <xsl:with-param name="string" select="$aftermatch" />
	<xsl:with-param name="match" select="$ucmatch"/>
      </xsl:call-template>
  </xsl:when>
  <xsl:when test="contains($aftermatch, $lcmatch)">
     <xsl:call-template name="highlight">
        <xsl:with-param name="string" select="$aftermatch" />
	<xsl:with-param name="match" select="$lcmatch"/>
      </xsl:call-template>
  </xsl:when>
  <xsl:when test="contains($aftermatch, $Match)">
     <xsl:call-template name="highlight">
        <xsl:with-param name="string" select="$aftermatch" />
	<xsl:with-param name="match" select="$Match"/>
      </xsl:call-template>
  </xsl:when>
  <xsl:otherwise>
    <xsl:value-of select="$aftermatch"/>
  </xsl:otherwise>
  </xsl:choose>
  
</xsl:template>

<xsl:template name="colorize">
  <xsl:param name="string"/>
  <xsl:param name="match"/>

 <!-- output string before match word, insert highlight tags -->
 <xsl:value-of select="substring-before($string, $match)"/>
   <xsl:element name="font">
    <xsl:attribute name="color">red</xsl:attribute>
     <xsl:element name="b"> 
        <xsl:value-of select="$match"/>
   </xsl:element>  <!-- b -->
  </xsl:element>   <!-- font -->
</xsl:template>




<!-- grab the search string from xql query -->
<xsl:template name="get-match" xmlns="html:xql:ino">
  <xsl:variable name="a">&apos;</xsl:variable>

   <xsl:variable name="tmpstring">
    <xsl:value-of select="substring-after($query, $a)"/>
  </xsl:variable> 
   <xsl:variable name="match1">
     <xsl:value-of select="translate(substring-before($tmpstring, $a),
	'*', '')"/> 
  </xsl:variable>
<!-- FIXME: what about wildcards like * ? 
    ... for now, just get rid of them (match the rest of it) -->

<!-- check for additional match string -->
   <xsl:variable name="remainder">
     <xsl:value-of select="substring-after($tmpstring, $a)"/>
   </xsl:variable>

   <xsl:choose>
   <xsl:when test="contains($remainder, $a)">
     <xsl:variable name="tmp2">
       <xsl:value-of select="substring-after($remainder, $a)"/>
     </xsl:variable>
    <xsl:variable name="match2">
    <xsl:value-of select="translate(substring-before($tmp2, $a), 
	'*', '')"/>
    </xsl:variable>
    <xsl:value-of select="concat($match1, '|', $match2)"/>
   </xsl:when>
   <xsl:otherwise>
    <xsl:value-of select="$match1"/>
   </xsl:otherwise>
  </xsl:choose>


<!-- TEMPORARY: until I figure out how to handle two matches!
    <xsl:value-of select="$match1"/>  -->

</xsl:template>



</xsl:stylesheet>
