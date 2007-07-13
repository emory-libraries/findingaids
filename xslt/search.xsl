<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0">

  <xsl:output method="xml"/>

  <xsl:include href="results.xsl"/>

  <xsl:template match="/">
    <xsl:apply-templates select="//repository"/>
  </xsl:template>

  <xsl:template match="repository">
    <!-- only display if the collection actually has content loaded -->
    <xsl:if test="@agencycode != ''">
      <option>
        <xsl:attribute name="value"><xsl:value-of select="@collection"/></xsl:attribute>
        <xsl:apply-templates/>
      </option>
    </xsl:if>
  </xsl:template>


</xsl:stylesheet>
