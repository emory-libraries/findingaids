<?xml version="1.0" encoding="ISO-8859-1"?> 

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:html="http://www.w3.org/TR/REC-html40" version="1.0"
	xmlns:ino="http://namespaces.softwareag.com/tamino/response2" 
	xmlns:xql="http://metalab.unc.edu/xql/">

<xsl:include href="ilnshared.xsl"/>

<!-- for range calculation -->
<xsl:param name="start">1</xsl:param> 

<xsl:variable name="mode_name">Search Results</xsl:variable> 
<xsl:variable name="curxsl" select="$xsl_search"/>

<xsl:variable name="match"><xsl:call-template name="get-match"/></xsl:variable> 
<xsl:variable name="total"><xsl:value-of select="//ino:cursor/@ino:count"/></xsl:variable>
<xsl:variable name="max"><xsl:call-template name="get-max"/></xsl:variable> 

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

<!--  TESTING: match string is <xsl:value-of select="$match"/>-->

     <xsl:element name="p">
       <xsl:attribute name="align">center</xsl:attribute>
	<xsl:element name="font">
	  <xsl:attribute name="size">+1</xsl:attribute>
	<xsl:choose>
	  <xsl:when test="$total = ''">
	    No matches found
          </xsl:when>
         <xsl:otherwise>
          <xsl:value-of select="$total" /> 
	match<xsl:if test="$total > 1">es</xsl:if> found
         </xsl:otherwise>
        </xsl:choose>
	</xsl:element>  <!-- font -->
     </xsl:element>  <!-- p -->


    <xsl:if test="$total > $max">
       <xsl:element name="p">
         <xsl:attribute name="align">center</xsl:attribute>
	  Displaying results <xsl:value-of select="$start"/> - 
	      <xsl:call-template name="get-last">
	          <xsl:with-param name="first" select="$start"/>
	      </xsl:call-template>. <xsl:element name="br"/>
  	<xsl:call-template name="next-previous"/>
       </xsl:element>  <!-- p -->
    </xsl:if>


    <!-- returning at the div2 (article/illustration) level -->
	<!-- pull out table of contents information -->


      <xsl:apply-templates select="//div2" />

    <xsl:if test="$total > $max">
       <xsl:element name="p">
         <xsl:attribute name="align">center</xsl:attribute>
	  <xsl:element name="br"/>
	<!-- navigation links again at bottom -->
  	<xsl:call-template name="next-previous"/>
       </xsl:element>  <!-- p -->
    </xsl:if>


  </xsl:element>  <!-- content div -->

  <!-- footer -->
  <xsl:copy-of
  select="document('http://chaucer.library.emory.edu/iln/foot.xml')"/> 

 </xsl:element> <!-- end body -->

 </xsl:element> <!-- end html -->
</xsl:template> <!-- / -->




<!-- generate links next/previous set of matches -->
<xsl:template name="next-previous">
  <xsl:variable name="first"><xsl:value-of 
	select="/ino:response/ino:cursor/ino:first/@ino:href"/></xsl:variable>
  <xsl:variable name="next"><xsl:value-of 
	select="/ino:response/ino:cursor/ino:next/@ino:href"/></xsl:variable>
  <xsl:variable name="prev"><xsl:value-of 
	select="/ino:response/ino:cursor/ino:prev/@ino:href"/></xsl:variable>
  <xsl:variable name="last"><xsl:value-of 
	select="/ino:response/ino:cursor/ino:last/@ino:href"/></xsl:variable>
  <xsl:variable name="xslt_start">&amp;xslt_start=</xsl:variable>

  More results: 

  <xsl:if test="$start != 1">  <!-- don't link to current page -->
    <xsl:element name="a">
      <xsl:attribute name="href"><xsl:value-of 
	select="concat($base_url, $first,
	$xslurl, $curxsl)"/>&amp;</xsl:attribute>1 - 
	<xsl:value-of select="$max"/></xsl:element> <!-- a -->
  </xsl:if>

  <xsl:if test="$prev != ''">
    <xsl:variable name="prev_start"><xsl:call-template
		name="get-start"><xsl:with-param name="href"
		select="$prev"/></xsl:call-template></xsl:variable>
   <xsl:if test="$prev_start != 1">  <!-- same as first, don't repeat -->
     |   <xsl:element name="a">
      <xsl:attribute name="href"><xsl:value-of 
   	select="concat($base_url, $prev, $xslurl, $curxsl, $xslt_start,
		$prev_start)"/></xsl:attribute><xsl:value-of
		select="$prev_start"/> -
	   <xsl:call-template name="get-last">
	      <xsl:with-param name="first" select="$prev_start"/>
           </xsl:call-template>
	</xsl:element> <!-- a -->
    </xsl:if>
  </xsl:if>

  <xsl:variable name="next_start"><xsl:call-template
		name="get-start"><xsl:with-param name="href"
		select="$next"/></xsl:call-template></xsl:variable>
  <xsl:if test="$next != ''">
     <xsl:if test="$start != 1"> | </xsl:if>  
	<!-- don't separate if this is first list -->
     <xsl:element name="a">
    <xsl:attribute name="href"><xsl:value-of 
	select="concat($base_url, $next, $xslurl, $curxsl, $xslt_start,
		$next_start)"/></xsl:attribute><xsl:value-of
	select="$next_start"/> - <xsl:call-template name="get-last">
	      <xsl:with-param name="first" select="$next_start"/>
           </xsl:call-template>
    </xsl:element> <!-- a -->
  </xsl:if>

  <xsl:variable name="last_start"><xsl:call-template
		name="get-start"><xsl:with-param name="href"
		select="$last"/></xsl:call-template></xsl:variable>
   <xsl:if test="($last_start != $next_start) and ($last_start != $start)"> 
       <!-- don't duplicate -->
   <xsl:variable name="last_last"><xsl:call-template
	name="get-last"><xsl:with-param name="first"
	select="$last_start"/></xsl:call-template></xsl:variable> 

     |   <xsl:element name="a">
      <xsl:attribute name="href"><xsl:value-of 
	select="concat($base_url, $last, $xslurl, $curxsl, $xslt_start,
	$last_start)"/></xsl:attribute><xsl:value-of
	select="$last_start"/> 
	<xsl:if test="$last_start != $last_last"> - <xsl:value-of
		select="$last_last"/>
	</xsl:if>
	</xsl:element> <!-- a -->
   </xsl:if>
</xsl:template>

<!-- get max # of elements returned -->
<xsl:template name="get-max">
  <xsl:variable name="comma">,</xsl:variable>
  <xsl:variable name="cparen">)</xsl:variable>
<!-- this seems like a hack way of getting this value... -->
  <xsl:variable name="href"><xsl:value-of 
	select="/ino:response/ino:cursor/ino:first/@ino:href"/></xsl:variable>

  <xsl:variable name="tmpstring">
    <xsl:value-of select="substring-after($href, $comma)"/>
  </xsl:variable> 

  <xsl:value-of select="substring-before($tmpstring, $cparen)"/> 

</xsl:template>


<!-- get start # of elements in href -->
<xsl:template name="get-start">
  <xsl:param name="href"/>
  <xsl:variable name="oparen">(</xsl:variable>
  <xsl:variable name="comma">,</xsl:variable>

  <xsl:variable name="tmpstring">
    <xsl:value-of select="substring-after($href, $oparen)"/>
  </xsl:variable> 

  <xsl:value-of select="substring-before($tmpstring, $comma)"/> 

</xsl:template>

<xsl:template name="get-last">
  <xsl:param name="first"/>
  
  <xsl:choose>
     <xsl:when test="($first + $max) > $total">
       <xsl:value-of select="$total"/>
     </xsl:when>
    <xsl:when test="$first = 1">
       <xsl:value-of select="$max"/>
    </xsl:when>
     <xsl:otherwise>
       <xsl:value-of select="($first + $max)"/>
     </xsl:otherwise>
  </xsl:choose>
</xsl:template>


</xsl:stylesheet>