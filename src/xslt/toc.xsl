<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
	xmlns:exist="http://exist.sourceforge.net/NS/exist" 
	exclude-result-prefixes="exist" 
	version="1.0">

  <!-- table of contents
       navigation within finding aid & to top-level (c01) series
       -->

  <xsl:template match="unitid"  mode="toc">
    <xsl:apply-templates mode="toc"/>
    <xsl:text>: &#x00A0;</xsl:text>
  </xsl:template>

  <!--  <xsl:template match="unittitle"  mode="toc">
    <xsl:apply-templates mode="toc"/> 
  </xsl:template> -->
  
  <xsl:template match="unitdate" mode="toc">
    <xsl:text> </xsl:text><xsl:apply-templates/>
  </xsl:template>
  
  <xsl:template match="ead/archdesc" mode="toc">
    <div id="tocAndDesc">
      <div id="toc" class="underlinedLinkBold">
        <p>Table of Contents:</p>

        <!-- No longer displayed in new layout [ title : link back to top-level of finding aid ] -->
      
      <!-- link to top-level information sections -->
      <ul>
        <li>
          <a title="Descriptive Summary">
            <xsl:attribute name="href">content.php?id=<xsl:value-of select="ancestor::ead/@id"/><xsl:value-of select="$url_suffix"/>#descriptiveSummary</xsl:attribute>
            Descriptive Summary
          </a>
          <!-- display number of keyword matches in this section if in kwic mode -->
          <xsl:apply-templates select="did/hits"/>
        </li>
        
        <li>
          <a title="Administrative Information">
            <xsl:attribute name="href">content.php?id=<xsl:value-of select="ancestor::ead/@id"/><xsl:value-of select="$url_suffix"/>#adminInfo</xsl:attribute>
            Administrative Information
          </a>
        </li>
        
        <li>
          <a title="Collection Description">
            <xsl:attribute name="href">content.php?id=<xsl:value-of select="ancestor::ead/@id"/><xsl:value-of select="$url_suffix"/>#collectionDesc</xsl:attribute>
            Collection Description
          </a>
          <xsl:apply-templates select="collectiondescription/hits"/>
        </li>
        
        <li>
          <a title="Selected Search Terms">
            <xsl:attribute name="href">content.php?id=<xsl:value-of select="ancestor::ead/@id"/><xsl:value-of select="$url_suffix"/>#searchTerms</xsl:attribute>
            Selected Search Terms
          </a>
          <!-- FIXME: could be called something else? value is here; include in toc query ? 
               <xsl:value-of select="//archdesc/controlaccess/head"/>
               -->
               <xsl:apply-templates select="controlaccess/hits"/>
             </li>

             <xsl:apply-templates select="index" mode="toc"/>

           </ul>
             
           <!-- display container list (no c01s) on left side column -->
           <xsl:if test="count(dsc/c01) = 0">
             <xsl:apply-templates select="dsc" mode="toc"/>
           </xsl:if>

         </div>

         <!-- if there are subseries, display on right side column -->
         <xsl:if test="count(dsc/c01)">
           <xsl:apply-templates select="dsc" mode="toc"/>
         </xsl:if>

       </div>

  </xsl:template>


  <xsl:template match="ead/archdesc/index" mode="toc">
    <li>
      <a>
        <xsl:attribute name="href">content.php?el=index&amp;id=<xsl:value-of select="@id"/></xsl:attribute>
        <xsl:value-of select="head"/>
      </a>
      <xsl:apply-templates select="hits"/>
    </li>
  </xsl:template>


  <!-- description of series / container list -->
  <xsl:template match="ead/archdesc/dsc" mode="toc">	
  <div id="descOfSeries" class="underlinedLink">
    <p>
      <xsl:element name="a">
        <xsl:attribute name="href">content.php?id=<xsl:value-of select="ancestor::ead/@id"/><xsl:value-of select="$url_suffix"/>#<xsl:value-of select="local-name()"/></xsl:attribute>
        <xsl:attribute name="title"><xsl:value-of select="head"/></xsl:attribute>
        <xsl:value-of select="head"/>
      </xsl:element>
      <xsl:apply-templates select="hits"/>
    </p>
    
    <xsl:if test="count(c01)">
      <ul class="bullet">		
        <xsl:apply-templates select="c01" mode="toc"/>
      </ul>
    </xsl:if>
  </div>
  </xsl:template>

  <!-- unused ? 
  <xsl:template match="ead/archdesc/*[not(self::bioghist)]" mode="toc" priority="-1">
    <xsl:element name="li">
      <a>
        <xsl:attribute name="href">content.php?id=<xsl:value-of select="ancestor::ead/@id"/><xsl:value-of select="$url_suffix"/>#<xsl:value-of select="local-name()"/></xsl:attribute>
        
        <xsl:value-of select="head"/>
      </a>
    </xsl:element>
  </xsl:template> -->

  <!-- container list (no subseries -->
  <xsl:template match="c01[not(c02)]" mode="toc">
    <xsl:if test="did/unittitle">
      <li>
        <xsl:apply-templates select="did/unittitle" mode="toc"/>
        <xsl:apply-templates select="did/unitdate" mode="toc"/>
      </li>
    </xsl:if>
  </xsl:template>


  <!-- series -->
  <xsl:template match="c01[c02]|c01[@level='series']" mode="toc">
    <xsl:element name="li">
      <!-- highlight this entry as the current one (currently displayed content)
           if the main content is this node or a child node -->
      <!--        <xsl:if test="//results/ead/c01/@id = ./@id or //results/ead/parent/@id = ./@id"> current</xsl:if> -->

      <xsl:if test="did/unittitle or not(did/container)">
          <xsl:attribute name="class">navbar</xsl:attribute>
          <a>
            <xsl:attribute name="href">content.php?el=<xsl:value-of select="local-name()"/>&amp;id=<xsl:value-of select="self::node()/@id"/><xsl:value-of select="$url_suffix"/></xsl:attribute>
            <xsl:apply-templates select="did/unitid" mode="toc"/>
            <xsl:apply-templates select="did/unittitle" mode="toc"/>
            <xsl:apply-templates select="did/unitdate" mode="toc"/>
          </a>
          <!-- display number of keyword matches in this section if in kwic mode -->
          <xsl:apply-templates select="hits"/>
          
      </xsl:if>
    </xsl:element>		
  </xsl:template>



<!-- don't highlight matches in the table of contents -->
<xsl:template match="exist:match" mode="toc">
  <xsl:variable name="txt"><xsl:value-of select="preceding::text()[0]"/></xsl:variable>
  <!-- for some reason, a single space between two matching terms is getting lost; put it back in here. -->
  <xsl:if test="preceding-sibling::exist:match and ($txt = '')">
    <xsl:text> </xsl:text>
  </xsl:if> 
  <xsl:apply-templates select="text()"/>
</xsl:template>

</xsl:stylesheet>
