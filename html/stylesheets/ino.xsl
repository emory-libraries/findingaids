<?xml version="1.0" ?>

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
   xmlns:ino="http://namespaces.softwareag.com/tamino/response2"
   xmlns:xql="http://metalab.unc.edu/xql/"
	 version="1.1">

<!-- tamino messages -->
<xsl:template match="ino:message">
<xsl:element name="p">
tamino message: <xsl:value-of select="ino:messagetext"/><br/><xsl:value-of select="ino:messageline"/><br/>
xql query: <xsl:value-of select="/.//xql:query"/><br/>

</xsl:element>
</xsl:template>



</xsl:stylesheet>


