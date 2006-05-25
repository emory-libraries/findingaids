<?xml version="1.0" encoding="ISO-8859-1"?> 

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:html="http://www.w3.org/TR/REC-html40" version="1.0"
	xmlns:ino="http://namespaces.softwareag.com/tamino/response2" 
	xmlns:xql="http://metalab.unc.edu/xql/">

<xsl:param name="image">0</xsl:param>  
<xsl:variable name="curxsl" select="imgview.xsl"/>

<xsl:output method="html"/>  

<xsl:template match="/">
  <xsl:processing-instruction name="cocoon-format">
    type="text/html"
  </xsl:processing-instruction>
<xsl:element name="html">

 <xsl:apply-templates select="//figure"/>

</xsl:element>

</xsl:template>


<xsl:template match="//figure">
<xsl:element name="head">
<xsl:variable name="quote">"</xsl:variable>
  <xsl:element name="title">Image Viewer</xsl:element>

  <xsl:element name="script">
    <xsl:attribute name="language">Javascript</xsl:attribute>
 	window.imagename ="http://chaucer.library.emory.edu/iln/images/ILN<xsl:value-of
							      select="./@entity" />.jpg";
	window.imagex = <xsl:value-of select="./@width" />;
	window.imagey = <xsl:value-of select="./@height" />;
     <xsl:choose>
      <xsl:when test="contains(./head, $quote)">
 	window.imagehead = "<xsl:call-template name="escape_quotes">
 	     <xsl:with-param name="string"
		select="normalize-space(./head)" /></xsl:call-template>";
      </xsl:when>
      <xsl:otherwise>
 	window.imagehead = "<xsl:value-of select="normalize-space(./head)" />"
	<!-- FIXME: still going to have a conflict with quotes...? -->
      </xsl:otherwise>
     </xsl:choose>

  </xsl:element> <!-- script -->   
</xsl:element>  <!-- head -->

<!-- frameset -->
<xsl:copy-of
select="document('http://vip.library.emory.edu/tamino/BECKCTR/ILN/non-xml/frameset.xml')" />

</xsl:template>


<xsl:template match="escape" name="escape_quotes">
  <xsl:param name="string" select="string()" /> 

 <xsl:variable name="realq">"</xsl:variable> 
 <xsl:variable name="q">\&quot;</xsl:variable>  
<!-- get string before the quote. -->
  <xsl:variable name="escape_string">  
   <xsl:choose>
     <xsl:when test="contains($string, $realq)">  
      <!-- output string before "; replace " with \&quot; -->
        <xsl:value-of select="substring-before($string,
		$realq)"/><xsl:value-of select="$q" />
      </xsl:when>
     <xsl:otherwise>
	<!-- shouldn't recurse if no quote, but print anyways -->
      <xsl:value-of select="$string" />
    </xsl:otherwise>
   </xsl:choose>
  </xsl:variable> 

   <!-- print out the first part of the string with new quote -->
   <xsl:value-of select="$escape_string" />
  <xsl:choose>
       <xsl:when test="contains($escape_string, $realq)">
<!-- 	<p>escape string is <xsl:value-of
select="$escape_string"/></p>   -->
<!-- 	<p>substring contains quote, recursing</p>  -->
  	  <xsl:call-template name="escape_quotes">
 	     <xsl:with-param name="string"
		select="substring-after($string, $realq)" />
	  </xsl:call-template>
<!-- 	     window.imagehead = "<xsl:value-of
select="$escape_string"/>";  -->
      </xsl:when> 
    <xsl:otherwise>
      <!-- now print out the escaped string -->
      <xsl:value-of select="substring-after($string, $realq)" />
    </xsl:otherwise>
  </xsl:choose> 
</xsl:template>


</xsl:stylesheet>