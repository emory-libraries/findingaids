<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
	xmlns:ino="http://namespaces.softwareag.com/tamino/response2"
	xmlns:xql="http://metalab.unc.edu/xql/"
	xmlns:cti="http://cti.library.emory.edu/"
	version="1.0">
	
	<xsl:import href="ino.xsl"/> 
	
	<xsl:param name="mode"/>
	<xsl:param name="label_text"/>
	<xsl:param name="baseLink"/>
	

	<xsl:template match="/">
		<xsl:call-template name="alphabox" select="/xq:result/results/alpha_list" />
		
		<xsl:apply-templates select="//record"/>
	</xsl:template>

			
	<xsl:template name="alphabox">
		<div class="blueBox">
			<span class="alphaText"><xsl:value-of select="$label_text" /></span>
			<p />
			<xsl:element name="span">
				<xsl:attribute name="class">alphaList</xsl:attribute>
				<xsl:element name="a">	
					<xsl:attribute name="href"><xsl:value-of select="$baseLink" />-all</xsl:attribute>ALL
				</xsl:element>
				<xsl:apply-templates select="//letter"/>
			</xsl:element>
		</div>	
		<p />
	</xsl:template>
	
	<xsl:template match="letter">
		<xsl:element name="span">
				<xsl:attribute name="class">alphaList</xsl:attribute>
				<xsl:element name="a">	
					<xsl:attribute name="href">
						<xsl:value-of select="$baseLink" />-<xsl:value-of select="." />
					</xsl:attribute>
					<xsl:value-of select="." />
				</xsl:element>
				<xsl:apply-templates select="letter" />
			</xsl:element>
	</xsl:template>
	
	<xsl:template match="record">
		<div>
			<xsl:element name="a">
				<xsl:attribute name="href">tamino-<xsl:value-of select="@id" /></xsl:attribute>
				<xsl:value-of select="unittitle" /> <xsl:value-of select="unitdate" />
			</xsl:element>
			<br />
								
			<xsl:apply-templates select="titleproper"/><br />
			<xsl:apply-templates select="physdesc/extent"/><br />
			<xsl:apply-templates select="abstract"/><br />
		</div><p />
	</xsl:template>
	
	<xsl:template match="titleproper | physdesc/extent | abstract">	
		<xsl:value-of select="." /> 
	</xsl:template>
	
</xsl:stylesheet>
