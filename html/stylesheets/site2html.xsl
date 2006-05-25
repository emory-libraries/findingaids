<?xml version="1.0" ?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	version="1.0">

<xsl:template match="/">
<xsl:element name="html">
<xsl:apply-templates select="./html/head"/>
<xsl:element name="body">
<xsl:attribute name="onload">MM_preloadImages('images/general-off.jpg')</xsl:attribute>
<xsl:apply-templates select="./html/_mapBody/heading"/>
<xsl:apply-templates select="./html//_mapBody/content"/>
<xsl:apply-templates select="./html//_mapBody/footing"/>
</xsl:element>
</xsl:element>
</xsl:template>

<xsl:template match="_mapBody/heading  | _mapBody/footing">
<xsl:apply-templates select="div" />
</xsl:template>

<xsl:template match="_mapBody/content">
<div class="content">
<xsl:apply-templates select="div/*"/>
<xsl:apply-templates select="footing"/>
</div>
</xsl:template>



<xsl:template match="@*|node()">
<xsl:if test="name()='table'">
</xsl:if>
            <xsl:copy>
              <xsl:apply-templates select="@*|node()"/>
            </xsl:copy>

</xsl:template>


</xsl:stylesheet>
