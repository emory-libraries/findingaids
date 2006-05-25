<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
    xmlns:xsp="http://apache.org/xsp"
		version="1.1">
<xsl:param name="identifier"/>
<xsl:param name="inoid"/>

<xsl:template match="xsp:page">
<xsl:apply-templates/>
</xsl:template>

<xsl:template match="frame">
<xsl:element name="frame">
<xsl:attribute name="name"><xsl:value-of select="name"/></xsl:attribute>
<xsl:attribute name="scrolling"><xsl:value-of select="scrolling"/></xsl:attribute>
<xsl:attribute name="marginheight"><xsl:value-of select="marginheight"/></xsl:attribute>
<xsl:attribute name="marginwidth"><xsl:value-of select="marginwidth"/></xsl:attribute>
<xsl:if test="noresize">
<xsl:attribute name="noresize"/>
</xsl:if>

<xsl:variable name="frameSrc">
<xsl:choose>
<xsl:when test="string-length($identifier)&gt;0">
<xsl:value-of select="normalize-space(src/text())"/><xsl:value-of select="$identifier"/>
</xsl:when>
<xsl:when test="string-length($inoid)&gt;0">
<xsl:value-of select="normalize-space(src/text())"/><xsl:value-of select="$inoid"/>
</xsl:when>
<xsl:otherwise>
<xsl:value-of select="normalize-space(src/text())"/>
</xsl:otherwise>
</xsl:choose>
</xsl:variable>

<xsl:variable name="frameSrcParam">
<xsl:for-each select="src/src-param">
<xsl:if test="position() &gt; 1">&amp;</xsl:if>
<xsl:if test="position() = 1">?</xsl:if>
<xsl:value-of select="@name"/>=<xsl:value-of select="normalize-space(.)"/>
</xsl:for-each>
</xsl:variable>
<xsl:attribute name="src"><xsl:value-of select="normalize-space($frameSrc)"/><xsl:value-of select="normalize-space($frameSrcParam)"/></xsl:attribute>

</xsl:element>


</xsl:template>

<xsl:template match="node() | @*" priority="-90">
<xsl:copy>
<xsl:apply-templates select="@*|node()"/>
</xsl:copy>
</xsl:template>

</xsl:stylesheet>
