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
	<xsl:param name="repository"/>

	

	<xsl:template match="/">
          <div class="navbox">
            <xsl:apply-templates select="//source" />
            <xsl:apply-templates select="//alpha_list" />
          </div>
		
		<xsl:apply-templates select="//record"/>
	</xsl:template>

        <xsl:template match="source">
          <div class="repositories">
            <h3>Filter by Repository:</h3>
            <ul>
              <li>
                <xsl:choose>
                  <xsl:when test="$repository = 'all'">
                    View All
                  </xsl:when>
                  <xsl:otherwise>
                    <a>
                      <xsl:attribute name="href"><xsl:value-of 
                      select="$baseLink"/></xsl:attribute>
                      View All
                    </a>
                  </xsl:otherwise>
                </xsl:choose>
              </li>
              <xsl:apply-templates/>
            </ul>
          </div>
        </xsl:template>

        <xsl:template match="source/repository">
            <!-- only display if the collection actually has content loaded -->
          <xsl:if test="@agencycode != ''">
          <li>
            <xsl:choose>
              <xsl:when test="@collection = $repository">
                <!-- if this is current repository, don't make it a link -->
                <xsl:apply-templates/>
              </xsl:when>
              <xsl:otherwise>
                <a>
                  <xsl:attribute name="href"><xsl:value-of 
                  select="concat($baseLink, '?repository=', @collection)"/></xsl:attribute>
                  <xsl:apply-templates/>
                </a>
              </xsl:otherwise>
            </xsl:choose>
          </li>
          </xsl:if>
        </xsl:template>

			
	<!--<xsl:template name="alphabox">-->
	<xsl:template match="alpha_list">
          <h3><xsl:value-of select="$label_text" /></h3>
            <xsl:element name="p">
              <xsl:attribute name="class">alphaList</xsl:attribute>
              <xsl:choose>
                <xsl:when test="$letter = 'all'">
                  ALL
                </xsl:when>
                <xsl:otherwise>
                  <xsl:element name="a">	
                    <xsl:attribute name="href"><xsl:value-of 
                    select="concat($baseLink, '?l=all&amp;repository=', $repository)" /></xsl:attribute>
                    ALL
                  </xsl:element>
                </xsl:otherwise>
              </xsl:choose>
              <xsl:apply-templates select="letter"/>
            </xsl:element>
        </xsl:template>
	
        <xsl:template match="letter">
          <xsl:element name="span">
            <xsl:attribute name="class">alphaList</xsl:attribute>
            <xsl:choose>
              <xsl:when test=". = $letter">
                <xsl:apply-templates/>
              </xsl:when>
              <xsl:otherwise>
                <xsl:element name="a">	
                <xsl:attribute name="href">
                  <xsl:value-of 
                    select="concat($baseLink, '?repository=', $repository, '&amp;l=', .)" /></xsl:attribute>
                <xsl:value-of select="." />
              </xsl:element>
            </xsl:otherwise>
          </xsl:choose>
          <xsl:apply-templates select="letter" />
        </xsl:element>

      </xsl:template>
	
	<xsl:template match="record">
		<div>			
			<xsl:apply-templates select="name"/>
			<xsl:apply-templates select="unittitle"/><br />
			<xsl:apply-templates select="physdesc"/>
			<xsl:apply-templates select="abstract"/><br />
			<xsl:apply-templates select="repository"/>
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

	<xsl:template match="abstract | unittitle">
		<xsl:apply-templates/> <xsl:text> </xsl:text> 		
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
	
        <!-- repository name -->
        <xsl:template match="repository">
          <xsl:apply-templates/>
          <xsl:text> </xsl:text>
          <!-- show an icon for each school, for better visual identification -->
          <xsl:choose>
            <xsl:when test="contains(., 'Emory')">
              <img src="images/emory-icon.png"/>
            </xsl:when>
            <xsl:when test="contains(., 'Boston')">
              <img src="images/boston-icon.png"/>
            </xsl:when>
            <xsl:otherwise/>
          </xsl:choose>
          <br />
        </xsl:template>

        <xsl:template match="repository/subarea">
          <xsl:text>, </xsl:text>
          <xsl:apply-templates/>
        </xsl:template>

        <!-- Wake Forest files -->
        <xsl:template match="repository/corpname">
          <xsl:apply-templates/>
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
	
</xsl:stylesheet>
