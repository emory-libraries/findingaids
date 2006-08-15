<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
	xmlns:exist="http://exist.sourceforge.net/NS/exist"
	xmlns:ino="http://namespaces.softwareag.com/tamino/response2"
	xmlns:xql="http://metalab.unc.edu/xql/"
	xmlns:cti="http://cti.library.emory.edu/"
	version="1.0">

<xsl:template match="unittitle"  mode="toc">
  <xsl:apply-templates select="*[not(self::unitdate)]|text()" mode="toc"/>
  <xsl:text> </xsl:text>
  <xsl:apply-templates select="unitdate" mode="toc"/> 

</xsl:template>

<xsl:template match="unitdate" mode="toc">
  <xsl:apply-templates/>
</xsl:template>

<xsl:template match="unitid" mode="toc">
  <xsl:apply-templates/>.
</xsl:template>


<xsl:template match="text()" mode="toc">
  <xsl:value-of select="."/>
</xsl:template>

<xsl:template match="ead/archdesc" mode="toc">
	<!--<div class="navbar">-->
	<!--<xsl:element name="emph">-->
        <div class="titleproper">	<!-- so title can be centered -->
          <a>
            <xsl:attribute name="href">section-content-<xsl:value-of select="ancestor::ead/@id"/><xsl:value-of select="$url_suffix"/></xsl:attribute>
            <xsl:value-of select="//ead/eadheader/filedesc/titlestmt/titleproper"/>
          </a>
        </div>
	<!--</xsl:element>-->
	<xsl:element name="span">
	<xsl:attribute name="class">toc-heading</xsl:attribute>
	<a name="a0">
	</a>
	</xsl:element>
	<xsl:element name="p">
	<xsl:attribute name="class">navbar</xsl:attribute>
	<a>
          <xsl:attribute name="href">section-content-<xsl:value-of select="ancestor::ead/@id"/><xsl:value-of select="$url_suffix"/>#descriptiveSummary</xsl:attribute>
	
	Descriptive Overview
	</a>

        <!-- display number of keyword matches in this section if in kwic mode -->
        <xsl:apply-templates select="hits"/>
        <!-- FIXME: why is this not matching the correct template? -->
        
	</xsl:element>

	
	<!-- remove details of ead header in toc 
	<a>
	<xsl:attribute name="href">section-content-<xsl:value-of select="ancestor::ead/@id"/>#descriptiveSummary</xsl:attribute>
	
	Descriptive Summary
	</a>
	</xsl:element>
	
	<xsl:element name="p">
	<xsl:attribute name="class">navbar</xsl:attribute>
	<a>
	<xsl:attribute name="href">section-content-<xsl:value-of select="ancestor::ead/@id"/>#adminInfo</xsl:attribute>
	
	Administrative Information
	</a>
	<ul class="navbar">
	<xsl:apply-templates select="acqinfo | accessrestrict | userestrict | prefercite | separatedmaterial" mode="toc"/>
	</ul>
	</xsl:element>
	
	<xsl:element name="p">
	<xsl:attribute name="class">navbar</xsl:attribute>
	<a>
	<xsl:attribute name="href">section-content-<xsl:value-of select="ancestor::ead/@id"/>#collectionDesc</xsl:attribute>
	
	Collection Description
	</a>
	<ul class="navbar">
	<xsl:apply-templates select="bioghist | scopecontent | arrangement | controlaccess " mode="toc"/>
	</ul>
	</xsl:element>
	-->
	<xsl:apply-templates select="dsc" mode="toc"/>
	<!--</div>-->
</xsl:template>

<xsl:template match="bioghist" mode="toc">
<xsl:element name="li">
<a>
  <xsl:attribute name="href">section-content-<xsl:value-of select="ancestor::ead/@id"/><xsl:value-of select="$url_suffix"/>#<xsl:value-of select="local-name(parent::node())"/>.<xsl:value-of select="position()"/></xsl:attribute>


<xsl:value-of select="head"/>
</a>
</xsl:element>
</xsl:template>

<xsl:template match="ead/archdesc/dsc" mode="toc">	
	<xsl:element name="a">
          <xsl:attribute name="href">section-content-<xsl:value-of select="ancestor::ead/@id"/><xsl:value-of select="$url_suffix"/>#<xsl:value-of select="local-name()"/></xsl:attribute>
		
		<xsl:value-of select="head"/>
	</xsl:element>
	<xsl:element name="ul">			
		<xsl:apply-templates select="c01" mode="toc"/>
	</xsl:element>
</xsl:template>

<xsl:template match="ead/archdesc/*[not(self::bioghist)]" mode="toc" priority="-1">
<xsl:element name="li">
<a>
  <xsl:attribute name="href">section-content-<xsl:value-of select="ancestor::ead/@id"/><xsl:value-of select="$url_suffix"/>#<xsl:value-of select="local-name()"/></xsl:attribute>

<xsl:value-of select="head"/>
</a>


</xsl:element>
</xsl:template>

<xsl:template match="c01[not(c02)]" mode="toc">
<!-- don't include the container list items in the table of contents, unless this is not toc mode (navbar creation)-->
<xsl:if test="did/unittitle and (not($mode = 'toc') )">

<xsl:element name="p"> 
<xsl:attribute name="class">navbar</xsl:attribute>

<xsl:apply-templates select="did/unittitle" mode="toc"/>
<xsl:apply-templates select="did/unitdate" mode="toc"/>

</xsl:element>
</xsl:if>
</xsl:template>


<xsl:template match="c01[c02]" mode="toc">
	<xsl:element name="li">
		<xsl:attribute name="class">navbar 
                <!-- mark this entry as the current one if the main content is this node or a child node -->
                <xsl:if test="//results/ead/c01/@id = ./@id or //results/ead/parent/@id = ./@id"> current</xsl:if>
               </xsl:attribute>

		<!-- don't include the container list items in the table of contents, unless this is not toc mode (navbar creation)-->
		<xsl:if test="did/unittitle and (not($mode = 'toc') or not(did/container))">
		
		<xsl:element name="p"> 
		<xsl:attribute name="class">navbar</xsl:attribute>
		<a>
                  <xsl:attribute name="href">section-content-<xsl:value-of select="local-name()"/>-<xsl:value-of select="self::node()/@id"/><xsl:value-of select="$url_suffix"/>#<xsl:apply-templates select="self::node()" mode="c-level-index"/></xsl:attribute>
		<xsl:if test="ancestor::dsc">
		
		</xsl:if>

		<xsl:apply-templates select="did/unitid" mode="toc"/>
		<xsl:apply-templates select="did/unittitle" mode="toc"/>
		<xsl:apply-templates select="did/unitdate" mode="toc"/>
		</a>

                <!-- display number of keyword matches in this section if in kwic mode -->
                <xsl:apply-templates select="hits"/>
		
		<!-- only display c01 levels in toc navbar, otherwise display the full table of contents -->
		<!-- toc is not coming back; some subtle xslt error (could be cpu), so only show c01 level
		<xsl:if test="not($mode = 'toc') and c02">
		<xsl:element name="ul">
		<xsl:attribute name="class">navbar</xsl:attribute>
		<xsl:apply-templates select="c02" mode="toc"/>
		</xsl:element>
		</xsl:if>
		-->
		
		</xsl:element>
		</xsl:if>
	</xsl:element>		
</xsl:template>

<!-- ============================================= -->
<xsl:template match="c02 | c03 | c04 | c05 |c06 | c07 | c08 | c09 | c10 | c11 | c12" mode="toc">
<!-- don't include the container list items in the table of contents-->
<xsl:if test="did/unittitle and not(did/container) and not(following-sibling::node()/did/container) ">

<xsl:element name="li"> 
<a>
  <xsl:attribute name="href">section-content-c01-<xsl:value-of select="ancestor::c01/@id"/><xsl:value-of select="$url_suffix"/>#<xsl:apply-templates select="ancestor-or-self::node()[self::c01 |self::c02 | self::c03 | self::c04 | self::c05 | self::c06 | self::c07 | self::c08 | self::c09]" mode="c-level-index"/></xsl:attribute>
<xsl:if test="ancestor::dsc">

</xsl:if>

<xsl:apply-templates select="did/unittitle" mode="toc"/>
<xsl:apply-templates select="did/unitdate" mode="toc"/>
</a>

<!-- Safari doesn't seem to format empty ul properly. May need to check for children before opening the ul element -->
<xsl:if test="c01 | c02 | c03 | c04 | c05 |c06 | c07 | c08 | c09 | c10 | c11 | c12">
<xsl:element name="ul">
<xsl:attribute name="class">navbar</xsl:attribute>

<xsl:apply-templates select="c03" mode="toc"/>
<!--
<xsl:apply-templates select="c01 | c02 | c03 | c04 | c05 |c06 | c07 | c08 | c09 | c10 | c11 | c12" mode="toc"/>
-->
</xsl:element>
</xsl:if>

</xsl:element>
</xsl:if>
</xsl:template>
<!-- ============================================= -->


<!-- for eXist only...
   in eXist, there is no way to restrict the count, so subtract the
   count from hits known to be in the c01 sections -->
<xsl:template match="archdesc/hits">
  <xsl:variable name="n"><xsl:value-of select=". - sum(//c01/hits)"/></xsl:variable> 
 <!-- don't display anything if there are zero hits -->
  <xsl:if test="$n > 0">
    <span class="hits">
      <xsl:value-of select="$n"/> hit<xsl:if test=". > 1">s</xsl:if>
    </span>
  </xsl:if>
</xsl:template>



<!-- don't highlight matches in the table of contents -->
<!-- FIXME: is this the correct behaviour? -->
<xsl:template match="exist:match" mode="toc">
  <xsl:variable name="txt"><xsl:value-of select="preceding::text()[0]"/></xsl:variable>
  <!--  DEBUG: preceding text is :<xsl:value-of select="$txt"/>:<br/>  -->
  <!-- for some reason, the single space between two matching terms is getting lost; put it back in here. -->
  <xsl:if test="preceding-sibling::exist:match and ($txt = '')">
    <xsl:text> </xsl:text>
  </xsl:if> 
  <xsl:apply-templates select="text()"/>
</xsl:template>

</xsl:stylesheet>
