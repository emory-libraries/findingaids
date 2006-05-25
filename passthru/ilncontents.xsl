<?xml version="1.0" encoding="ISO-8859-1"?> 

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:html="http://www.w3.org/TR/REC-html40" version="1.0"
	xmlns:ino="http://namespaces.softwareag.com/tamino/response2" 
	xmlns:xql="http://metalab.unc.edu/xql/">
	
<xsl:include href="ilnshared.xsl"/>

<xsl:variable name="mode_name">Browse</xsl:variable> 
<xsl:variable name="begin_idxql">?_xql=TEI.2//div2[@id='</xsl:variable>
<xsl:variable name="end_idxql">']</xsl:variable>
<xsl:variable name="curxsl" select="$xsl_contents"/>

<!-- used in other modes -->
<xsl:variable name="max">0</xsl:variable>
<xsl:variable name="start">0</xsl:variable>

<xsl:variable name="sortby"><xsl:call-template name="get-sortby"/></xsl:variable>

<!-- should not be used in content mode; xslt complains if not defined -->
<xsl:variable name="match">0</xsl:variable>


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


<!-- FIXME: should browse/contents start by volume & then go to articles? -->
<!-- pull out table of contents according to whatever was requested -->
    <xsl:choose>
  <!-- check for div2 first, since it contains div1 in the xpath -->
      <xsl:when test="contains($query, '/div2')">
	 <!-- sort-by options -->
	  <xsl:call-template name="sortby-options"/>
        <xsl:apply-templates select="//div2" />    
      </xsl:when>
      <xsl:when test="contains($query, '//div1')">
        <xsl:apply-templates select="//div1" />    
      </xsl:when>
      <xsl:when test="contains($query, '//figure')">
	 <!-- sort-by options: do we need this for the illustrations? -->
<!--	  <xsl:call-template name="sortby-options"/>  -->
        <xsl:apply-templates select="//figure" />  
      </xsl:when>
    <xsl:otherwise>
     TESTING: did not properly detect mode
    </xsl:otherwise>
    </xsl:choose>
  </xsl:element>  <!-- content div -->

  <!-- footer -->
  <xsl:copy-of
  select="document('http://chaucer.library.emory.edu/iln/foot.xml')"/> 

 </xsl:element> <!-- end body -->

 </xsl:element> <!-- end html -->
</xsl:template> <!-- / -->


<xsl:template match="div1"> 

 <xsl:element name="p">
  <xsl:element name="a">
   <xsl:attribute name="href"><xsl:value-of
select="$base_url"/>?_xql=TEI.2//div1[@id='<xsl:value-of select="./@id"/>']/div2&amp;_xslsrc=xsl:stylesheet/ilncontents.xsl</xsl:attribute>  
  <xsl:apply-templates select="head"/>
 </xsl:element> <!-- end a -->
 <xsl:element name="font">
 <xsl:attribute name="size">-1</xsl:attribute>
  - <xsl:value-of select="./@type"/>
  - <xsl:value-of select="docDate" /> 
  - (<xsl:value-of select="count(div2)"/> Articles)
  </xsl:element> <!-- end font -->
 </xsl:element> <!-- end p -->
</xsl:template>



<xsl:template name="sortby-options">

<!-- FIXME: should current mode not be linked? -->
<p align="center"><font size="-1">
Sort by: 
  <xsl:choose>
   <xsl:when test="$sortby = '@type'">
    <a href="javascript:reSort('bibl/date/@value')">Date</a> | 
    Article Type |
    <a href="javascript:reSort('head')">Title</a>
   </xsl:when>
   <xsl:when test="$sortby = 'head'">
    <a href="javascript:reSort('bibl/date/@value')">Date</a> | 
    <a href="javascript:reSort('@type')">Article Type</a> |
    Title
   </xsl:when>
   <xsl:otherwise>  <!-- Date is default -->
    Date | 
    <a href="javascript:reSort('@type')">Article Type</a> |
    <a href="javascript:reSort('head')">Title</a>
   </xsl:otherwise>
 </xsl:choose>
</font></p>

</xsl:template>

<xsl:template name="get-sortby" xmlns="html:xql:ino">
  <xsl:variable name="query">
<xsl:value-of select="normalize-space(ino:response/xql:query)"/></xsl:variable>

  <xsl:if test="contains($query, 'sortby')">
   <xsl:variable name="tmpstring">
    <xsl:value-of select="substring-after($query, 'sortby(')"/>
  </xsl:variable> 
  <xsl:value-of select="substring-before($tmpstring, ')')"/> 
  </xsl:if>


</xsl:template>




</xsl:stylesheet>