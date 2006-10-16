<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
	version="1.0">

  <!-- summary mode:
       brief display of series & subseries (hits if keyword search)
       -->

  <xsl:template match="dsc/head" mode="summary">
    <h2><xsl:value-of select="text()"/></h2>		
  </xsl:template>
	
  <xsl:template match="c01|c02|c03" mode="summary">
    <p> 
    <xsl:attribute name="class"><xsl:value-of select="local-name()"/></xsl:attribute>  
      <xsl:element name="a">
        <xsl:attribute name="href">content.php?el=<xsl:value-of select="local-name()"/>&amp;id=<xsl:value-of select="self::node()/@id"/><xsl:value-of select="$url_suffix"/></xsl:attribute>			
        <xsl:value-of select="did/unitid"/>
        <xsl:text>: &#x00A0;</xsl:text>
        <xsl:value-of select="did/unittitle"/>
      </xsl:element>
      
      <!-- note: hits are *inside* heading to keep them on the same line -->      
      
      <!-- if we have the full-text, count matches under this node -->
      <xsl:variable name="count"><xsl:value-of select="count(.//exist:match)"/> </xsl:variable>
      
      <xsl:choose>
        <xsl:when test="$count > 0">
          <span class="hits"><xsl:value-of select="$count"/> hit<xsl:if test="$count > 1">s</xsl:if></span>
        </xsl:when>
        <!-- if not full-text, use results from exist match-count -->
        <xsl:when test="local-name() != 'c01' and hits > 0">
          <!-- FIXME : temporary fix because of a bug in eXist's match-count; 
               correctly detects hits / no hits in subseries, but count is inaccurate. -->
          <span class="hits">hits</span>
        </xsl:when>
        <xsl:otherwise>
          <xsl:apply-templates select="hits"/>
        </xsl:otherwise>
      </xsl:choose>
    </p>             

      <!-- FIXME: how to get did/physdesc here for pdf output ?
           output with id & hide with css? -->

    <!-- if there are subseries, indent to display hierarchy -->
    <xsl:if test="count(c02[@level='subseries']) + count(c03[@level='subseries']) > 0">
      <div class="indent">
        <xsl:apply-templates select="c02[@level='subseries']|c03[@level='subseries']" mode="summary"/>
      </div>
    </xsl:if>
  </xsl:template>

	
</xsl:stylesheet>
