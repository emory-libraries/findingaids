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
		<h3>
			<xsl:attribute name="class">indent</xsl:attribute>
			<!--<xsl:apply-templates select="unitid" mode="summary"/>-->

			<xsl:element name="a">
                          <xsl:attribute name="href">section-content-<xsl:value-of select="local-name()"/>-<xsl:value-of select="self::node()/@id"/><xsl:value-of select="$url_suffix"/>#<xsl:apply-templates select="self::node()" mode="c-level-index"/></xsl:attribute>			
				<xsl:value-of select="did/unitid"/>: <xsl:value-of select="did/unittitle"/>
			</xsl:element>
		</h3>
		<br/>
	</xsl:template>

<!--
	<xsl:template match="unitid" mode="summary">
		UNITID is great<xsl:value-of select="."/>
	</xsl:template>
-->
	<xsl:template match="c02 | c03 | c04 | c05 |c06 | c07 | c08 | c09 | c10 | c11 | c12" mode="summary">
	</xsl:template>
	
	<xsl:template match="scopecontent" mode="summary"></xsl:template>
	<xsl:template match="physdec" mode="summary"></xsl:template>
	
</xsl:stylesheet>
