<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0">

  <xsl:output method="xml"/>

  <xsl:template match="/">
    <xsl:apply-templates select="//repository"/>
  </xsl:template>

  <xsl:template match="repository">
    <option>
      <xsl:attribute name="value"><xsl:value-of select="."/></xsl:attribute>
      <xsl:apply-templates/>
    </option>
  </xsl:template>

  <!--
        <xsl:choose>
          <xsl:when test=". = 'Boston College, John J. Burns Library, Archives and Manuscripts'">boston</xsl:when>
          <xsl:otherwise>emory</xsl:otherwise>
        </xsl:choose>
-->

</xsl:stylesheet>
