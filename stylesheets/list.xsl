<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0">

  <xsl:output method="xml"/>

  <xsl:template match="/">
    <xsl:if test="count(//li) > 0">
      <ul>
        <xsl:apply-templates select="//li"/>
      </ul>
    </xsl:if>
  </xsl:template>

  <xsl:template match="li">
    <xsl:copy-of select="."/>
  </xsl:template>

</xsl:stylesheet>
