<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
	xmlns:cti-map="http://cti.library.emory.edu/sitemap#"
	version="1.1">

<!-- heading and footing elements -->

<xsl:template match="_mapBody/heading |footing" mode="style">
            <xsl:copy-of select="."/>
</xsl:template>
</xsl:stylesheet>
