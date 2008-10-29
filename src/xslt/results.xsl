<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
	xmlns:exist="http://exist.sourceforge.net/NS/exist"
	xmlns:ino="http://namespaces.softwareag.com/tamino/response2"
	xmlns:xql="http://metalab.unc.edu/xql/"
	xmlns:cti="http://cti.library.emory.edu/"
	version="1.0">
	
  <!--	<xsl:import href="ino.xsl"/>  -->
	
	<xsl:param name="mode"/>
	<xsl:param name="label_text"/>
	<xsl:param name="baseLink"/>
	<xsl:param name="url_suffix"/>
	<xsl:param name="letter"/>

	<xsl:template match="/">
		<xsl:apply-templates select="//alpha_list" />
		
		<xsl:apply-templates select="//record"/>
	</xsl:template>

			
	<!--<xsl:template name="alphabox">-->
	<xsl:template match="alpha_list">
		<div id="alphalist">
                  <h4><xsl:value-of select="$label_text" /></h4>
		  
		  <xsl:element name="a">	
		    <xsl:if test="$letter = 'all' or $letter = ''">
		      <xsl:attribute name="class">current</xsl:attribute>
		    </xsl:if>
		    <xsl:attribute name="href"><xsl:value-of select="$baseLink" />?l=all</xsl:attribute>ALL
		    <xsl:apply-templates select="letter"/>
		  </xsl:element>
		</div>	
	</xsl:template>
	
	<xsl:template match="letter">
	  <xsl:element name="a">	
	    <xsl:if test=". = $letter">
	      <xsl:attribute name="class">current</xsl:attribute>
	    </xsl:if>
	    <xsl:attribute name="href">
	      <xsl:value-of select="$baseLink" />?l=<xsl:value-of select="." />
	    </xsl:attribute>
	    <xsl:value-of select="." />
	    <xsl:apply-templates select="letter" />
	  </xsl:element>
	</xsl:template>
	
	<xsl:template match="record">
		<div>			
			<xsl:apply-templates select="name"/>
			<xsl:apply-templates select="unittitle"/><br />
			<xsl:apply-templates select="physdesc"/>
			<xsl:apply-templates select="abstract"/>
			<xsl:apply-templates select="matches" />
		</div><p />
	</xsl:template>

	<xsl:template match="persname | corpname | famname ">	
		<xsl:element name="a">
                  <xsl:attribute name="href">content.php?id=<xsl:value-of select="ancestor::record/@id" /><xsl:value-of select="$url_suffix" /></xsl:attribute>			
			<xsl:value-of select="." />
		</xsl:element>
		<br />
	</xsl:template>	
	
	<xsl:template match="unittitle[not(../name/node())]">	
		<xsl:element name="a">
			<xsl:attribute name="href">content.php?id=<xsl:value-of select="ancestor::record/@id" /><xsl:value-of select="$url_suffix" /></xsl:attribute>			
			<xsl:value-of select="." />
		</xsl:element>
	</xsl:template>	

	<xsl:template match="unittitle">
		<xsl:apply-templates/> <xsl:text> </xsl:text> 		
	</xsl:template>		

        <xsl:template match="abstract">	<!-- break is here so it won't appear if there is no abstract -->
		<xsl:apply-templates/> <xsl:text> </xsl:text><br />
	</xsl:template>		


        <!-- add a space before unitdate (bulk date or circa) -->
	<xsl:template match="unitdate">
		 <xsl:text> </xsl:text> <xsl:apply-templates/>
	</xsl:template>		

        <xsl:template match="physdesc">
          <xsl:apply-templates/>
          <br />
        </xsl:template>

        <xsl:template match="physdesc/extent">	
          <xsl:text> </xsl:text> <xsl:apply-templates/>
        </xsl:template>
	
	<xsl:template match="matches">
          <xsl:value-of select="total" /> match<xsl:if test="total > 1">es</xsl:if>
		<!--
		(
		<xsl:element name="a">
			<xsl:attribute name="href">section-kwic-<xsl:value-of select="../@id" /></xsl:attribute>
			view search term
		</xsl:element> in context
		)
		-->
		<br />
	</xsl:template>


        <!-- italicize titles anywhere in result summary -->
        <xsl:template match="title">
          <i><xsl:apply-templates/></i>
        </xsl:template>
	
</xsl:stylesheet>
