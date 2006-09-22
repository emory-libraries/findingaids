<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
	xmlns:exist="http://exist.sourceforge.net/NS/exist" 
	exclude-result-prefixes="exist" 
	version="1.0">

  <xsl:import href="toc.xsl"/> 
  <xsl:import href="summary.xsl"/> 
  
  <!-- unused?  <xsl:param name="mode"/> -->
  
  <!-- any parameters to be added to urls within the site (e.g., for passing keywords) -->
  <xsl:param name="url_suffix"/>

  <!-- strings for translating case -->
  <xsl:variable name="lowercase" select="'abcdefghijklmnopqrstuvwxyz'"/>
  <xsl:variable name="uppercase" select="'ABCDEFGHIJKLMNOPQRSTUVWXYZ'"/>

  
  <xsl:template match="/">
    <div id="toc">	
      <h1>Table of Contents</h1>
      <hr/>
      <xsl:apply-templates select="//toc/ead/archdesc" mode="toc"/>
    </div>
    
    <!--start content-->
    <div id="content">
      <xsl:apply-templates select="//results/ead/eadheader/filedesc/titlestmt"/>
      <xsl:apply-templates select="//results/ead/*"/>		
    </div>
      
  </xsl:template>

  <!-- eadheader : top-level finding aid information -->
  <xsl:template match="ead/eadheader">
    <xsl:element name="div">
      <xsl:attribute name="id">eadheader</xsl:attribute>
      <xsl:apply-templates select="//publicationstmt"/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="titlestmt">
    <div id="headingBlock">
      <xsl:apply-templates select="titleproper | subtitle"/>
    </div>
  </xsl:template>

  <!-- unused in our documents? -->
  <xsl:template match="titlestmt/subtitle">
    <xsl:element name="span">
      <xsl:attribute name="class">content_subtitle</xsl:attribute>
      <xsl:apply-templates/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="publicationstmt/publisher">
    <h3><xsl:apply-templates/></h3>
  </xsl:template>

  <xsl:template match="publicationstmt/address">
    <h4><xsl:apply-templates/></h4>
  </xsl:template>

 <xsl:template match="addressline">
   <xsl:apply-templates/><br/>
 </xsl:template> 


  <!-- date encoded; currently not displayed -->
  <xsl:template match="publicationstmt/date"/>

  <!-- archive description -->
  <xsl:template match="ead/archdesc">
    <div class="content">
      <xsl:apply-templates select="did" />
      <hr/>
      <xsl:element name="h2">
        <a>
          <xsl:attribute name="name">adminInfo</xsl:attribute>
          Administrative Information
        </a> 
      </xsl:element>
      <xsl:apply-templates select="acqinfo | accessrestrict | userestrict | prefercite | separatedmaterial"/>
      <hr/>
      <xsl:element name="h2">
        <a>
          <xsl:attribute name="name">collectionDesc</xsl:attribute>
          Collection Description
        </a>
      </xsl:element>
      <xsl:apply-templates select="bioghist | scopecontent | arrangement"/>
      <hr/>
      <xsl:apply-templates select="controlaccess"/>
      <hr/>
      <xsl:apply-templates select="dsc"/>
    </div>
  </xsl:template>
  

  <xsl:template match="archdesc/did">
    <xsl:element name="h2">
      <a>
        <xsl:attribute name="name">descriptiveSummary</xsl:attribute>	
        Descriptive Summary
      </a>
    </xsl:element>
    
    <table id="descriptivesummary">
      <col width="20%" align="left" valign="top"/>
      <col width="80%" align="left" valign="top"/>
      <xsl:apply-templates mode="table"/>
    </table>
    
  </xsl:template>

  <!-- separate extents with a space -->
  <xsl:template match="extent">
    <xsl:text> </xsl:text><xsl:apply-templates/>
  </xsl:template>

  <!-- set off repository subarea -->
  <xsl:template match="subarea">
    <xsl:text>, </xsl:text>
    <xsl:apply-templates/>
  </xsl:template>

  <!-- descriptive summary elements -->
  <xsl:template match="archdesc/did/*" mode="table">
    <xsl:variable name="name"><xsl:value-of select="local-name()"/></xsl:variable>
    <tr>
      <td valign="top">
        <xsl:choose>
          <!-- display name based on element name -->
          <xsl:when test="$name = 'unittitle'">Title:</xsl:when>
          <xsl:when test="$name = 'unitid'">Call Number:</xsl:when>
          <xsl:when test="$name = 'physdesc'">Extent:</xsl:when>
          <xsl:when test="$name = 'origination'">Creator:</xsl:when>
          <xsl:when test="$name = 'langmaterial'">Language:</xsl:when>
          <xsl:otherwise>
            <!-- use element name for label; capitalize the first letter -->
            <xsl:value-of select="concat(translate(substring($name,1,1),$lowercase, $uppercase),substring($name, 2, (string-length($name) - 1)))"/>: 
          </xsl:otherwise>
        </xsl:choose>
      </td>
      <td>
        <xsl:apply-templates/>
      </td>
    </tr>
  </xsl:template>


  <!-- lower-level headings within archive description -->
  <xsl:template match="archdesc//head[not(ancestor::dsc) and not(ancestor::controlaccess)]">
    <xsl:element name="h3">
      <a>
        <xsl:attribute name="name"><xsl:value-of select="local-name(parent::node())"/></xsl:attribute>
        <xsl:apply-templates/>
      </a>
    </xsl:element>
  </xsl:template>  


  <!-- top-level control access heading -->
  <xsl:template match="archdesc/controlaccess/head">
    <h2>
      <a name="searchTerms">
        <xsl:apply-templates/>
      </a>
    </h2>
  </xsl:template>

  <!-- sub-level control access headings -->
  <xsl:template match="controlaccess/controlaccess/head">
    <h4>
      <xsl:apply-templates/>
    </h4>
  </xsl:template>
  

  <xsl:template match="controlaccess/persname | controlaccess/famname | controlaccess/title">
    <xsl:apply-templates/>
    <br/>
  </xsl:template>


  <xsl:template match="dsc">
    <a>
      <xsl:attribute name="name"><xsl:value-of select="local-name()"/></xsl:attribute>
    </a>
    <xsl:choose>
      <!-- if at least 2 c levels exist, do a toc display -->
      <xsl:when test="c01/c02 or c01[@level='series']">
        <xsl:apply-templates mode="summary"/>
      </xsl:when>
      
      <!-- otherwise, display the full container list -->
      <!-- if there are no c02s then process all c01s with containers. Ignore the c01s that are headings -->
      <xsl:otherwise>
        <xsl:element name="h2">
          <xsl:apply-templates select="head"/>
        </xsl:element>
        <a>
          <xsl:attribute name="name">series<xsl:number/></xsl:attribute>
        </a>
        <table>
          <xsl:attribute name="border">0</xsl:attribute>
          <col width="7%" align="left" valign="top"/>
          <col width="7%" align="left" valign="top"/>
          <col width="86%"/>
          <!-- process container c01s -->
          <xsl:apply-templates select="c01/did" mode="table"/>
        </table>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>


  <xsl:template match="title">
    <i><xsl:apply-templates/></i>
  </xsl:template>

  <xsl:template match="physdesc">
    <xsl:element name="h3">
      <xsl:apply-templates/>
    </xsl:element>
  </xsl:template>


<!-- lists unused in our documents ? -->
  <xsl:template match="list">
    <xsl:element name="ul">
      <xsl:apply-templates/> 
    </xsl:element>
  </xsl:template>

  <xsl:template match="item">
    <xsl:element name="li">
      <xsl:apply-templates/>
    </xsl:element>
  </xsl:template>


  <xsl:template match="p | bibref">
    <p class="indent">
      <xsl:apply-templates/>
    </p>
  </xsl:template>

  <xsl:template match="subject |corpname[not(parent::origination)] |  genreform | geogname | occupation">
    <xsl:element name="span">
      <xsl:attribute name="class">indent</xsl:attribute>
      <xsl:apply-templates/>
    </xsl:element>
    <br/>
  </xsl:template>

  <!-- in case of multiple languages, spaces are getting lost around the "and"; put spaces back in here -->
  <xsl:template match="langmaterial/language">
    <xsl:if test="preceding-sibling::language">
      <xsl:text> </xsl:text>
    </xsl:if>
    <xsl:apply-templates/>
    <xsl:if test="following-sibling::language">
      <xsl:text> </xsl:text>
    </xsl:if>
  </xsl:template>


  <!-- highest c-level in return set -->
  <xsl:template match="c01|c02|c03">
    
    <!-- process only at this container level, not sub-containers -->
    <xsl:element name="h2">
      <xsl:apply-templates select="did/unitid"/>
      <br/>
      <xsl:text> </xsl:text>
      <xsl:apply-templates select="did/unittitle"/>
      <xsl:text> </xsl:text>
      <xsl:apply-templates select="did/unitdate"/>
      <br/>
      <xsl:value-of select="did/physdesc"/>
    </xsl:element>
    
    <xsl:apply-templates select="scopecontent"/>
    <xsl:apply-templates select="bibliography"/>
    <xsl:apply-templates select="bioghist"/>
    <xsl:apply-templates select="arrangement"/>

    <xsl:choose>
      <!-- if there are subseries, use summary mode -->
      <xsl:when test="c02[@level='subseries'] or c03[@level='subseries']">
        <xsl:apply-templates select="c02|c03" mode="summary"/>
      </xsl:when>
      <!-- otherwise, display normally -->
      <xsl:otherwise>
        <table width="100%">
          <col width="55px" align="left" valign="top"/>
          <col width="55px" align="left" valign="top"/>
          <!-- process sub-container (only one level down) -->
          <xsl:apply-templates select="*/did" mode="table"/>
        </table>
      </xsl:otherwise>
    </xsl:choose>
    
  </xsl:template>

  <!-- c0# dids : box and folder containers  -->
  <xsl:template match="did[container/@type='box']" mode="table"> 
  
    <!-- only show box/folder once for the whole page -->
    <xsl:if test="count(../preceding-sibling::node()/did[container]) = 0">
      <tr>
        <th align="left" valign="top">Box</th>
        <th align="left">Folder</th>
      </tr> 
    </xsl:if>
    
    <tr>
      <td valign="top">
        <xsl:apply-templates select="container[@type='box']" mode="table"/>
      </td>
      <td valign="top">
        <xsl:apply-templates select="container[@type='folder']" mode="table"/>
      </td>
      <td valign="top">
        <xsl:apply-templates select="unitid"/>
        <xsl:text> </xsl:text>
        <xsl:apply-templates select="unittitle"/>
        <xsl:apply-templates select="physdesc"/>
        <xsl:apply-templates select="abstract"/>
        <xsl:apply-templates select="note"/>
      </td>
    </tr>
  </xsl:template>

  <!-- container of volumes -->
  <xsl:template match="did[container/@type='volume']" mode="table">
    <!-- if new volume number, print volume, folder header -->
    <xsl:if test="not(../preceding-sibling::node()[1]/did/container[@type='volume'])"> 
      <tr>
        <th>Volume</th>
      </tr>
    </xsl:if>

    <tr>
      <td valign="top">
        <xsl:apply-templates select="container[@type='volume']" mode="table"/>
      </td>
      <td valign="top">
      </td>
      <td valign="top">
        <xsl:apply-templates select="unitid"/>
        <xsl:text> </xsl:text>
        <xsl:apply-templates select="unittitle"/>
        <xsl:apply-templates select="physdesc"/>
        <xsl:apply-templates select="abstract"/>
        <xsl:apply-templates select="note"/>
      </td>
    </tr>
  </xsl:template>

  <!-- scope and content and arrangement -->
  <xsl:template match="c01/scopecontent | c01/arrangement">
    <xsl:apply-templates />
  </xsl:template>

  <xsl:template match="scopecontent[parent::c01|parent::c02]/head | arrangement[parent::c01|parent::c02]/head">
    <h3><xsl:value-of select="."/></h3>
  </xsl:template>

  <!-- c level without containers, used as a heading to following siblings -->
    <xsl:template match="did[not(container)]" mode="table">
      <tr>
        <td colspan="3">
          <h4><xsl:apply-templates/></h4>
        </td>
      </tr>
    </xsl:template>



<!-- highlight keyword matches -->
<xsl:template match="exist:match">
  <xsl:variable name="txt"><xsl:value-of select="preceding::text()[0]"/></xsl:variable>
  <!-- for some reason, the single space between two matching terms is getting lost; put it back in here. -->
  <xsl:if test="preceding-sibling::exist:match and ($txt = '')">
    <xsl:text> </xsl:text>
  </xsl:if> 

  <span class="match"><xsl:apply-templates/></span>
</xsl:template>


<!-- display number of keyword matches -->
<xsl:template match="hits">
 <!-- don't display anything if there are zero hits -->
  <xsl:if test=". != 0">
    <span class="hits">
      <xsl:apply-templates/> hit<xsl:if test=". > 1">s</xsl:if>
    </span>
  </xsl:if>
</xsl:template>


</xsl:stylesheet>
