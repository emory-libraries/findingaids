<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0">

  <xsl:output method="xml"/>

  <xsl:variable name="docname">
    <xsl:value-of select="substring-before(/ead/eadheader/eadid, '.xml')"/>
  </xsl:variable>

  <xsl:template match="/">
    <xsl:apply-templates />
  </xsl:template>

  <xsl:template match="@*|node()">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()|processing-instruction()|comment()"/>
    </xsl:copy>
  </xsl:template>


  <xsl:template match="c01[@level='series'] | c02[@level='subseries'] | c03[@level='subseries']">
    <xsl:variable name="seriesid">
      <xsl:apply-templates select="did/unitid" mode="id"/>
    </xsl:variable>

    <!-- add a human-readable id based on the unitid (e.g., series # or subseries #.#) -->

    <xsl:copy>
      <xsl:attribute name="id">
        <xsl:value-of select="concat($docname, '_', $seriesid)"/>
      </xsl:attribute>

      <xsl:apply-templates select="@*|node()|processing-instruction()|comment()"/>
    </xsl:copy>
  </xsl:template>


  <!-- strings for translating case -->
  <xsl:variable name="lowercase" select="'abcdefghijklmnopqrstuvwxyz'"/>
  <xsl:variable name="uppercase" select="'ABCDEFGHIJKLMNOPQRSTUVWXYZ'"/>

  <xsl:variable name="space" select="' '"/>
  <xsl:variable name="nospace" select="''"/>

  <xsl:template match="unitid" mode="id">
    <xsl:value-of select="translate(translate(., $uppercase, $lowercase), $space, $nospace)"/>
  </xsl:template>

</xsl:stylesheet>
