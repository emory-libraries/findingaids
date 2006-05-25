<?xml version="1.0" encoding="ISO-8859-1"?>  

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:html="http://www.w3.org/TR/REC-html40" version="1.0"
	xmlns:ino="http://namespaces.softwareag.com/tamino/response2" 
	xmlns:xql="http://metalab.unc.edu/xql/">

<xsl:include href="ilnshared.xsl"/>
<xsl:include href="teihtml-tables.xsl"/>

<xsl:param name="pos">0</xsl:param>
<xsl:param name="xql">0</xsl:param>
<xsl:param name="rmode">0</xsl:param>
<xsl:param name="range">0</xsl:param>

<!-- not actually used in browse mode -->
<xsl:variable name="max">0</xsl:variable>
<xsl:variable name="start">0</xsl:variable>

<xsl:variable name="match"><xsl:call-template name="get-match"/></xsl:variable> 
<xsl:variable name="mode_name">Browse</xsl:variable> 
<xsl:variable name="begin_idxql">?_xql=TEI.2//div2[@id='</xsl:variable>
<xsl:variable name="end_idxql">']</xsl:variable>
<xsl:variable name="begin_posxql">?_xql=TEI.2<xsl:choose>
<xsl:when test="contains($xql, 'sortby')">
<xsl:value-of select="substring-before($xql, 'sortby')"/>
</xsl:when>
<xsl:otherwise>
<xsl:value-of select="$xql"/>
</xsl:otherwise>
</xsl:choose>[</xsl:variable>
<xsl:variable name="end_posxql">]<xsl:if test="contains($xql, 'sortby')">sortby<xsl:value-of select="substring-after($xql, 'sortby')"/></xsl:if></xsl:variable>
<xsl:variable name="curxsl" select="$xsl_browse"/>

 <xsl:output method="html"/>  

<xsl:template match="/"> 
 <xsl:call-template name="proc_instr" /> 

  <xsl:element name="html"> 
 <xsl:call-template name="html_head" /> 
<!-- begin body -->
  <xsl:element name="body">

  <!-- NOTE: these files must be well-formed xml or nothing will show up-->
  <!-- header -->
  <xsl:copy-of
  select="document('http://chaucer.library.emory.edu/iln/head.xml')" />
  <!-- sidebar -->
  <xsl:copy-of
  select="document('http://chaucer.library.emory.edu/iln/sidebar.xml')" />

  <xsl:element name="div">
     <xsl:attribute name="class">content</xsl:attribute>
	<xsl:call-template name="html_title" /> 
     <!-- should be returning one div2; display contents --> 

      <xsl:apply-templates select="//div2" />
   <!-- links to next & previous matches (if specified) -->
  <xsl:call-template name="next-prev" />
  </xsl:element>  <!-- content div -->


  <!-- footer -->
  <xsl:copy-of
  select="document('http://chaucer.library.emory.edu/iln/foot.xml')"/> 

 </xsl:element> <!-- end body -->

 </xsl:element> <!-- end html -->
</xsl:template> <!-- / -->




<!-- print out the content-->
<xsl:template match="div2">
<!-- get everything under this node -->
  <xsl:apply-templates/> 
</xsl:template>

<!-- display the title -->
<xsl:template match="head">
  <xsl:element name="h1">
     <!-- explicitly colorize keywords in the title -->
   <xsl:call-template name="default"/>
  </xsl:element>
</xsl:template>

<xsl:template match="bibl">
  <xsl:element name="i">
    <xsl:value-of select="title"/>,
  </xsl:element>
  <xsl:value-of select="biblScope[@type='volume']"/>,
  <xsl:value-of select="biblScope[@type='issue']"/>,
  <xsl:value-of select="biblScope[@type='pages']"/>.<br/>
  <p><xsl:value-of select="date"/></p>
</xsl:template>

<xsl:template match="p/title">
  <xsl:element name="i">
    <xsl:call-template name="default"/>
  </xsl:element>
</xsl:template>  

<xsl:template match="p">
  <xsl:element name="p">
    <xsl:apply-templates/> 
  </xsl:element>
</xsl:template>

<xsl:template match="q">
  <xsl:element name="blockquote">
    <xsl:apply-templates/> 
  </xsl:element>
</xsl:template>


<!-- convert rend tags to their html equivalents 
     so far, converts: center, italic 		  -->
<xsl:template match="//*[@rend]">
  <xsl:choose>
    <xsl:when test="@rend='center'">
      <xsl:element name="center">
        <xsl:apply-templates/>
      </xsl:element>
    </xsl:when>
    <xsl:when test="@rend='italic'">
      <xsl:element name="i">
        <xsl:apply-templates/>
      </xsl:element>
    </xsl:when>
    <xsl:when test="@rend='smallcaps'">
      <xsl:element name="span">
	<xsl:attribute name="class">smcaps</xsl:attribute>
        <xsl:apply-templates/>
      </xsl:element>
    </xsl:when>
  </xsl:choose>
</xsl:template>

<xsl:template match="lb">
  <xsl:element name="br" />
</xsl:template>





<!-- generate next & previous links (if variables are defined) -->
<xsl:template name="next-prev">

  <xsl:variable name="next"><xsl:value-of 
	select="/ino:response/ino:cursor/ino:next/@ino:href"/></xsl:variable>
  <xsl:variable name="prev"><xsl:value-of 
	select="/ino:response/ino:cursor/ino:prev/@ino:href"/></xsl:variable>

 <xsl:element name="table">
  <xsl:attribute name="width">85%</xsl:attribute>
  <xsl:element name="tr">
   <xsl:element name="td">
    <xsl:attribute name="width">33%</xsl:attribute>
    <xsl:attribute name="align">left</xsl:attribute>

  <xsl:if test="$prev != ''">
        <xsl:element name="a">
	   <xsl:attribute name="href"><xsl:value-of
		select="concat($base_url, $prev)"/><xsl:value-of 
		select="concat($xslurl,$xsl_browse)"/>&amp;xslt_xql=<xsl:value-of select="$xql"/>&amp;xslt_rmode=<xsl:value-of select="$rmode"/><xsl:if test="$range != 0">&amp;xslt_range=<xsl:value-of select="$range"/></xsl:if></xsl:attribute>&lt;&lt; Previous article</xsl:element>  <!-- a -->
  </xsl:if>
 </xsl:element> <!-- td -->

 <xsl:element name="td">
    <xsl:attribute name="width">33%</xsl:attribute>
   <xsl:attribute name="align">center</xsl:attribute>
<!-- output "back to list" link if return mode is defined -->
  <xsl:if test="$rmode != 0">
   <xsl:element name="a">
     <xsl:attribute name="href"><xsl:value-of
	select="$base_url"/>?_xql<xsl:if test="$range != 0">(<xsl:value-of select="$range"/>)</xsl:if>=<xsl:value-of
	select="$xql"/><xsl:value-of select="concat($xslurl, $rmode)"/>
    </xsl:attribute>Back to List
   </xsl:element> <!-- a -->
  </xsl:if>
 </xsl:element> <!-- td -->


  <xsl:element name="td">
        <xsl:attribute name="width">33%</xsl:attribute>
	<xsl:attribute name="align">right</xsl:attribute>
    
  <xsl:if test="$next != ''">
        <xsl:element name="a">
	   <xsl:attribute name="href"><xsl:value-of
	select="concat($base_url, $next)"/><xsl:value-of
	select="concat($xslurl,$xsl_browse)"/>&amp;xslt_xql=<xsl:value-of select="$xql"/>&amp;xslt_rmode=<xsl:value-of select="$rmode"/><xsl:if test="$range != 0">&amp;xslt_range=<xsl:value-of select="$range"/></xsl:if></xsl:attribute>Next article &gt;&gt;</xsl:element>  

  </xsl:if> 
  </xsl:element> <!-- td -->

  </xsl:element> <!-- tr -->
  </xsl:element> <!-- table -->
</xsl:template>




</xsl:stylesheet>