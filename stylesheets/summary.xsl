<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
	xmlns:ino="http://namespaces.softwareag.com/tamino/response2"
	xmlns:xql="http://metalab.unc.edu/xql/"
	xmlns:cti="http://cti.library.emory.edu/"
	version="1.0">

	<xsl:template match="dsc/head" mode="summary">
		<h2><xsl:value-of select="text()"/></h2>		
		<xsl:apply-templates select="c01" mode="summary"/>
	</xsl:template>
	
	<xsl:template match="c01" mode="summary">
		
<!--	</xsl:template>	
	<xsl:template match="unittitle"  mode="summary">	-->
		<p>
                  <h4>
			<xsl:attribute name="class">indent</xsl:attribute>
			<!--<xsl:apply-templates select="unitid" mode="summary"/>-->

			<xsl:element name="a">
                          <xsl:attribute name="href">content.php?el=<xsl:value-of select="local-name()"/>&amp;id=<xsl:value-of select="self::node()/@id"/><xsl:value-of select="$url_suffix"/></xsl:attribute>			
				<xsl:value-of select="did/unitid"/>: <xsl:value-of select="did/unittitle"/>
			</xsl:element>
                        <xsl:apply-templates select="hits"/></h4>
		</p>
                <xsl:apply-templates select="c02" mode="summary"/>
	</xsl:template>

<!--
	<xsl:template match="unitid" mode="summary">
		UNITID is great<xsl:value-of select="."/>
	</xsl:template>
-->

	<xsl:template match="c02|c03" mode="summary">
          <p>
            <h4>
              <xsl:attribute name="class"><xsl:value-of select="local-name()"/></xsl:attribute>
              <xsl:element name="a">
                <xsl:attribute name="href">content.php?el=<xsl:value-of select="local-name()"/>&amp;id=<xsl:value-of select="self::node()/@id"/><xsl:value-of select="$url_suffix"/></xsl:attribute>			
                <xsl:apply-templates select="did/unitid"/>: <xsl:apply-templates select="did/unittitle"/>
              </xsl:element>
              <!-- FIXME : temporary fix because of a bug in eXist's match-count;
                   correctly detects hits / no hits in subseries, but count is inaccurate.
              <xsl:apply-templates select="hits"/> -->
              <xsl:if test="hits > 0">
                <span class="hits">hits</span>
              </xsl:if>


            </h4>
            </p>

            <xsl:apply-templates select="c03" mode="summary"/>
	</xsl:template>

	<xsl:template match="c04 | c05 |c06 | c07 | c08 | c09 | c10 | c11 | c12" mode="summary">
	</xsl:template>
	
	<xsl:template match="scopecontent" mode="summary"></xsl:template>
	<xsl:template match="physdec" mode="summary"></xsl:template>
	
</xsl:stylesheet>
