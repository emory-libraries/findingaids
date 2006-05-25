<?xml version="1.0" encoding="ISO-8859-1"?> 

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:html="http://www.w3.org/TR/REC-html40" version="1.0"
	xmlns:ino="http://namespaces.softwareag.com/tamino/response2" 
	xmlns:xq="http://metalab.unc.edu/xq/">

<xsl:param name="mode">article</xsl:param>
<!-- param for flat mode: all volumes or single volume -->
<xsl:param name="vol">all</xsl:param>
<xsl:variable name="image_url">http://chaucer.library.emory.edu/iln/images/</xsl:variable>
<xsl:variable name="mode_name">Browse</xsl:variable> 
<xsl:variable name="xslurl">&#x0026;_xslsrc=xsl:stylesheet/</xsl:variable>
<xsl:variable name="xsl_imgview">imgview.xsl</xsl:variable>
<xsl:variable name="query"><xsl:value-of select="ino:response/xq:query"/></xsl:variable>
<xsl:variable name="total_count" select="count(//div1 | //div2[figure])" />

<xsl:variable name="cookie_name"><xsl:value-of select="concat('ILN-', $mode)"/></xsl:variable>

<!-- <xsl:include href="ilnshared.xsl"/> -->

<xsl:output method="xml"/>  

<xsl:template match="/"> 

  <!-- begin body -->
  <xsl:element name="body">
    <xsl:if test="$mode != 'flat'">
    <xsl:attribute name="onload">load_status(<xsl:value-of 
 select="$total_count"/>, '<xsl:value-of select="$cookie_name"/>')</xsl:attribute>  
     <xsl:attribute name="onunload">store_status(<xsl:value-of 
 select="$total_count"/>, '<xsl:value-of select="$cookie_name"/>')</xsl:attribute>  
    </xsl:if>

  <xsl:element name="noscript">
  <i>Note: This site works best with Javascript enabled.</i>
	<!-- ensure that all text is displayed -->
      <style type="text/css">
	ul.contents { display: block } 
        img.javascript { display: none }
      </style>
    <xsl:if test="$mode != 'flat'">
      <p>Because you do not have Javascript running, you may prefer to browse <a href='volume.php' rel='alternate'>volumes</a> separately.</p>
    </xsl:if>
  </xsl:element> <!-- noscript -->

  <xsl:choose>
    <xsl:when test="$mode = 'flat'">
       <xsl:choose>
         <xsl:when test="$vol = 'all'">
           <xsl:apply-templates select="//div1" mode="flat"/>
         </xsl:when>    
         <xsl:when test="$vol = 'single'">
           <xsl:apply-templates select="//div2" mode="flat"/>
         </xsl:when>    
       </xsl:choose>
     </xsl:when>
    <xsl:otherwise>
      <xsl:apply-templates select="//div1[1]"/>
    </xsl:otherwise>
  </xsl:choose>
  <!-- note: applying only to the first div1, in order to count and
  increment list number, which is needed for all collapsible lists -->

</xsl:element>  <!-- end body -->

</xsl:template>


<xsl:template match="div1"> 
  <xsl:param name="num" select="1"/>	<!-- collapsible list id number -->

  <xsl:element name="p"> 
   <!-- create toggle image -->
   <xsl:element name="a">
     <xsl:attribute name="class">toggle</xsl:attribute>
     <xsl:attribute name="onclick">toggle_ul('list<xsl:value-of select="$num"/>')</xsl:attribute>
     <xsl:element name="img">
       <xsl:attribute name="alt">&#x00BB;</xsl:attribute>
       <xsl:attribute name="src">images/closed.gif</xsl:attribute>
       <xsl:attribute name="id">gif_list<xsl:value-of select="$num"/></xsl:attribute>
     </xsl:element> <!-- img -->
   </xsl:element> <!-- a -->

   <!-- make volume title clickable also -->
   <xsl:element name="a">
     <xsl:attribute name="onclick">toggle_ul('list<xsl:value-of select="$num"/>')</xsl:attribute>
     <xsl:apply-templates select="head"/> <!-- title -->
   </xsl:element> <!-- a -->
   <xsl:element name="font">
     <xsl:attribute name="size">-1</xsl:attribute>
     <!-- type information is redundant at volume level -->
     <!--  - <xsl:value-of select="./@type"/> -->   <!-- type (volume) -->
      - <xsl:value-of select="docDate" />  <!-- date -->
      - 
      <xsl:choose>
        <xsl:when test="$mode = 'figure'">
           (<xsl:value-of select="count(figure)"/> Illustrations) <!-- number of figures -->
        </xsl:when>
    	<xsl:otherwise>
           (<xsl:value-of select="count(div2)"/> Articles,  <!-- number of articles -->
	   <xsl:value-of select="count(.//figure)"/> Illustrations)
        </xsl:otherwise>
      </xsl:choose> 
    </xsl:element> <!-- end font -->
  </xsl:element>  <!-- end p -->

 <xsl:element name="ul">
   <xsl:attribute name="id">list<xsl:value-of select="$num"/></xsl:attribute>
   <xsl:attribute name="class">contents</xsl:attribute>
   <xsl:choose>
     <xsl:when test="$mode = 'figure'">
       <xsl:element name="table">
         <xsl:apply-templates select="figure"/>
       </xsl:element> <!-- table -->
     </xsl:when>
     <xsl:otherwise>
       <xsl:apply-templates select="div2[1]">
  <!-- number of lists before current div1, plus one for current div -->
         <xsl:with-param name="num" select="$num + 1"/>
       </xsl:apply-templates>
     </xsl:otherwise>
   </xsl:choose>

   <!-- close list link at end of list -->
   <xsl:element name="a">
     <xsl:attribute name="onclick">toggle_ul('list<xsl:value-of select="$num"/>')</xsl:attribute>
	close list
   </xsl:element> <!-- a -->

 </xsl:element>

 <xsl:apply-templates select="following-sibling::div1[1]">
 <!-- count all figures in current div, number before current div1,
      plus one for current div -->
   <xsl:with-param name="num" select="count(div2[figure]) + $num + 1"/>
 </xsl:apply-templates>

</xsl:template>  <!-- div1 -->



<!-- articles with figures - creates a collapsible sublist with thumbnails -->
<xsl:template match="div2[figure]"> 
  <xsl:param name="num"/>	<!-- collapsible list id -->

 <xsl:element name="li">
   <xsl:attribute name="class">container</xsl:attribute>
   <!-- create toggle image -->
   <xsl:element name="a">
     <xsl:attribute name="class">toggle</xsl:attribute>
     <xsl:attribute name="onclick">toggle_ul('list<xsl:value-of select="$num"/>')</xsl:attribute>
     <xsl:element name="img">
       <xsl:attribute name="src">images/closed.gif</xsl:attribute>
       <xsl:attribute name="alt"> &#x00BB; </xsl:attribute>
       <xsl:attribute name="id">gif_list<xsl:value-of select="$num"/></xsl:attribute>
     </xsl:element> <!-- img -->
   </xsl:element> <!-- a -->
   
  <xsl:element name="a">
   <xsl:attribute name="href">browse.php?id=<xsl:value-of select="@id"/></xsl:attribute>  
   <xsl:call-template name="cleantitle"/>
  </xsl:element> <!-- a -->

  <xsl:call-template name="div2-bibl"/>
</xsl:element> <!-- end li -->

<xsl:element name="ul">
  <xsl:attribute name="id">list<xsl:value-of
select="$num"/></xsl:attribute>
   <xsl:attribute name="class">contents</xsl:attribute>
   <xsl:element name="table">
    <xsl:apply-templates select="figure"/>
   </xsl:element> <!-- table -->
</xsl:element>

<xsl:apply-templates select="following-sibling::div2[1]">
  <xsl:with-param name="num" select="$num + 1"/>
</xsl:apply-templates>

</xsl:template>


<!-- articles without any illustrations -->
<xsl:template match="div2"> 
 <!-- count of collapsible lists, to pass on to div2s with figures -->
  <xsl:param name="num"/>

 <xsl:element name="li">
   <xsl:attribute name="class">contents</xsl:attribute>
   <xsl:element name="a">
     <xsl:attribute name="href">browse.php?id=<xsl:value-of select="@id"/></xsl:attribute>  
     <xsl:call-template name="cleantitle"/>
   </xsl:element> <!-- a -->

   <xsl:call-template name="div2-bibl"/>
 </xsl:element> <!-- end li -->

 <xsl:apply-templates select="following-sibling::div2[1]">
 <!-- just pass num, don't increment: only count div1s & div2s with figures -->
   <xsl:with-param name="num" select="$num"/>
 </xsl:apply-templates>

</xsl:template>


<!--display figure & link to image-viewer  (slightly different than ilnshared) -->
<xsl:template match="figure">
      <xsl:element name="tr">
        <xsl:element name="td">
          <xsl:attribute name="class">figure</xsl:attribute>

<!-- javascript version of the image & link -->

      <xsl:element name="a">
	<xsl:attribute
name="href">javascript:launchViewer('figure.php?id=<xsl:value-of
select="./@entity"/>')</xsl:attribute>

<xsl:element name="img">
  <xsl:attribute name="class">javascript</xsl:attribute>
  <xsl:attribute name="src"><xsl:value-of select="concat($image_url, 'ILN', @entity, '.gif')"/></xsl:attribute>
  <xsl:attribute name="alt">view image</xsl:attribute>
  <xsl:attribute name="title"><xsl:value-of select="normalize-space(head)"/></xsl:attribute>
  </xsl:element> <!-- end img -->
  </xsl:element> <!-- end a --> 


<!-- non-javascript version of image & link -->
<!-- note: if neither javascript nor css works, there will be two
   copies of image (but other things will probably be broken also) -->
  <noscript>
      <xsl:element name="a">
<!--  <xsl:attribute name="href"><xsl:value-of
select="concat($image_url, 'ILN', @entity, '.jpg')"/></xsl:attribute> -->
	<xsl:attribute name="href">figure.php?id=<xsl:value-of select="./@entity"/></xsl:attribute>
        <xsl:attribute name="target">image_viewer</xsl:attribute>
        <!-- open a new window without javascript -->
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
    </xsl:element> <!-- end p -->

  </xsl:element> <!-- end td -->
  </xsl:element> <!-- end tr --> 
</xsl:template>

<!-- flat contents: list of volumes -->
<xsl:template match="div1" mode="flat">
 <xsl:element name="p">
     <!-- make volume title clickable also -->
   <xsl:element name="a">
     <xsl:attribute name="href">volume.php?id=<xsl:value-of select="@id"/></xsl:attribute>
     <xsl:apply-templates select="head"/> <!-- title -->
   </xsl:element> <!-- a -->
   <xsl:element name="font">
     <xsl:attribute name="size">-1</xsl:attribute>
     <!-- type information is redundant at volume level -->
     <!--  - <xsl:value-of select="./@type"/> -->   <!-- type (volume) -->
      - <xsl:value-of select="docDate" />  <!-- date -->
     - (<xsl:value-of select="count[@type='article']"/> Articles,  <!-- number of articles -->
	 <xsl:value-of select="count[@type='figure']"/> Illustrations)
    </xsl:element> <!-- end font -->
  </xsl:element>  <!-- end p -->
</xsl:template>


<!-- flat contents: articles & illustrations in a single volume -->
<xsl:template match="div2" mode="flat"> 

 <xsl:element name="li">
   <xsl:attribute name="class">contents</xsl:attribute>
   <xsl:element name="a">
     <xsl:attribute name="href">browse.php?id=<xsl:value-of select="@id"/></xsl:attribute>  
     <xsl:call-template name="cleantitle"/>
   </xsl:element> <!-- a -->

   <xsl:call-template name="div2-bibl"/>

   <xsl:if test=".//figure">
     <xsl:element name="ul">
       <xsl:element name="table">
          <xsl:apply-templates select="figure"/>
      </xsl:element> <!-- table -->
     </xsl:element>
   </xsl:if>

  </xsl:element> <!-- end li -->
</xsl:template>

 <!-- Use n attribute (normalized caps) for article title; if n is blank, 
      label as untitled; used by all div2 variants -->
<xsl:template name="cleantitle">
  <xsl:choose>
    <xsl:when test="@n = ''">
      <xsl:text>[Untitled]</xsl:text>
    </xsl:when>
    <xsl:otherwise>
      <xsl:value-of select="normalize-space(./@n)"/>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<!-- bibl output : used by all div2 variants -->
<xsl:template name="div2-bibl">
   <xsl:element name="font">
     <xsl:attribute name="size">-1</xsl:attribute>
     - <xsl:value-of select="./@type"/>
     - <xsl:value-of select="bibl/date" /> 
     <xsl:if test="bibl/extent">
       - (<xsl:value-of select="bibl/extent" />)
     </xsl:if>
    </xsl:element> <!-- end font -->
</xsl:template>


</xsl:stylesheet>
