<?xml version="1.0" encoding="ISO-8859-1"?> 

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:html="http://www.w3.org/TR/REC-html40" version="1.0"
	xmlns:ino="http://namespaces.softwareag.com/tamino/response2" 
	xmlns:xql="http://metalab.unc.edu/xql/">

<xsl:include href="ilnshared.xsl"/>

<xsl:param name="term">0</xsl:param>
<xsl:param name="term2">0</xsl:param>
<xsl:param name="term3">0</xsl:param>

<!-- construct string to pass search term values to browse via url -->
<xsl:variable name="term_string"><xsl:if test="$term != 0">&amp;term=<xsl:value-of select="$term"/></xsl:if><xsl:if test="$term2 != 0">&amp;term2=<xsl:value-of select="$term2"/></xsl:if><xsl:if test="$term3 != 0">&amp;term3=<xsl:value-of select="$term3"/></xsl:if></xsl:variable>

<xsl:output method="xml"/>  

<xsl:template match="/"> 
    <!-- returning at the div2 (article/illustration) level -->
    <!-- pull out table of contents information -->

    <xsl:choose>
      <xsl:when test="//div2/count">
        <xsl:element name="table">
          <xsl:attribute name="class">searchresults</xsl:attribute>
	  <xsl:element name="tr">
	    <xsl:element name="th"/>
	    <xsl:element name="th">number of matches</xsl:element>
	  </xsl:element>
          <xsl:apply-templates select="//div2" mode="count"/>
        </xsl:element>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates select="//div2" />
      </xsl:otherwise>
    </xsl:choose>

</xsl:template> <!-- / -->


<!-- put article title in a table in order to align matches count off to the side -->
<xsl:template match="div2" mode="count">
  <xsl:element name="tr">
    <xsl:element name="td">
      <xsl:apply-templates select="."/>
    </xsl:element>
    <xsl:element name="td">
      <xsl:attribute name="class">count</xsl:attribute>
	<!-- number of matches for a search -->
      <xsl:apply-templates select="count"/>
    </xsl:element>
  </xsl:element>
</xsl:template>



</xsl:stylesheet>
