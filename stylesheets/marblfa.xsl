<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
  xmlns:exist="http://exist.sourceforge.net/NS/exist" 
  exclude-result-prefixes="exist" 
  version="1.0">

  <xsl:import href="toc.xsl"/> 
  <xsl:import href="summary.xsl"/> 
  
  <xsl:param name="mode"/>
  <!-- any parameters to be added to urls within the site (e.g., for passing keywords) -->
  <xsl:param name="url_suffix"/>

  <!-- strings for translating case -->
  <xsl:variable name="lowercase" select="'abcdefghijklmnopqrstuvwxyz'"/>
  <xsl:variable name="uppercase" select="'ABCDEFGHIJKLMNOPQRSTUVWXYZ'"/>
  
  <xsl:template match="/">
    <xsl:choose>
      <xsl:when test="$mode = 'full'">
        <xsl:apply-templates/>
      </xsl:when>
      <xsl:otherwise>
        <div id="toc">	
          <h1>Table of Contents</h1>
          <hr/>
          <xsl:apply-templates select="//toc/ead/archdesc" mode="toc"/>

          <hr/>
        <a>
          <xsl:attribute name="href">pdf.php?id=<xsl:value-of select="//ead/@id"/></xsl:attribute>
          printable copy (PDF)
        </a>

        </div>

        <!--start content-->
        <div id="content">
          <!--          <xsl:apply-templates select="//results/ead/eadheader/filedesc/titlestmt"/>-->
          <xsl:apply-templates select="//results/ead"/>		
        </div>
        
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="titlestmt">
    <div id="title">
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

  <xsl:template match="archdesc/did/unitid">
    <span id="unitid"><xsl:apply-templates/></span>
  </xsl:template>

  <xsl:template match="publicationstmt">
    <div id="publicationstmt">
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <xsl:template match="publicationstmt/publisher">
    <h3><xsl:apply-templates/></h3>
  </xsl:template>

  <xsl:template match="publicationstmt/address">
    <h4><xsl:apply-templates/></h4>
  </xsl:template>

 <xsl:template match="addressline">
   <p class="tight"><xsl:apply-templates/></p>
 </xsl:template> 

 <!-- templates to ignore for now -->
 <xsl:template match="eadid|author|publicationstmt/date|profiledesc"/>

  <!-- date document was encoded; currently not displayed -->
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
     
     <!-- display the following fields, in this specific order -->
     <xsl:apply-templates select="accessrestrict"/>
     <xsl:apply-templates select="userestrict"/>
     <xsl:apply-templates select="altformavail"/>
     <xsl:apply-templates select="originalsloc"/>
     <xsl:apply-templates select="bibliography"/>
     <xsl:apply-templates select="relatedmaterial"/>
     <xsl:apply-templates select="separatedmaterial"/>
     <xsl:apply-templates select="acqinfo"/>
     <xsl:apply-templates select="custodhist"/>
     <xsl:apply-templates select="prefercite"/>
     
     <hr/>
     
     <xsl:element name="h2">
       <a>
         <xsl:attribute name="name">collectionDesc</xsl:attribute>
         Collection Description
       </a>
     </xsl:element>
     <!-- display the following fields, in this specific order -->
     <xsl:apply-templates select="bioghist"/>
     <xsl:apply-templates select="scopecontent"/>
     <xsl:apply-templates select="arrangement"/>
     <xsl:apply-templates select="otherfindaid"/>
     
     
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
      <xsl:apply-templates/>
    </table>

 </xsl:template>

 <xsl:template match="archdesc/did/*">
   <xsl:variable name="name"><xsl:value-of select="local-name()"/></xsl:variable>
   
   <xsl:variable name="label">
     <xsl:choose>
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
   </xsl:variable>
   
   <tr>
     <th>
       <xsl:value-of select="$label"/>
     </th>
     <td>
       <xsl:apply-templates/>
     </td>
   </tr>
   
 </xsl:template>

  <xsl:template match="physdesc">
    <xsl:element name="h3">
      <xsl:apply-templates/>
    </xsl:element>
  </xsl:template>

 <!-- separate extents with a space -->
 <xsl:template match="extent">
   <xsl:text> </xsl:text><xsl:apply-templates/>
 </xsl:template>

 <!-- set off repository subarea from main -->
 <xsl:template match="subarea">
   <xsl:text>, </xsl:text> <xsl:apply-templates/>
 </xsl:template>

 <xsl:template match="archdesc/*[not(self::did) and not(self::dsc)]">
   <div>
     <xsl:apply-templates/>
   </div>
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
    <p class="tight">
      <xsl:apply-templates/>
    </p>
  </xsl:template>

  <xsl:template match="subject |corpname[not(parent::origination)] |  genreform | geogname | occupation">
    <p class="tight">
      <xsl:apply-templates/>
    </p>
  </xsl:template>

  <xsl:template match="dsc">
    <div class="pagebreak">
      <a>
        <xsl:attribute name="name"><xsl:value-of select="local-name()"/></xsl:attribute>
      </a>
      <xsl:choose>
        <!-- when there are series & subseries, do a summary display -->
        <xsl:when test="c01/c02 or c01[@level='series']">
          <xsl:apply-templates mode="summary"/>
          <xsl:if test="$mode = 'full'">
            <!-- then display full info -->
            <xsl:apply-templates select="c01"/>
          </xsl:if>
        </xsl:when>
        <!-- otherwise, display the full container list -->
        <!-- if there are no c02s then process all c01s with containers. Ignore the c01s that are headings -->
        <xsl:otherwise>
          <a>
            <xsl:attribute name="name">series<xsl:number/></xsl:attribute>
            <xsl:apply-templates select="head"/> 
          </a>
          <table>
            <xsl:attribute name="border">0</xsl:attribute>
            <col width="7%" align="left" valign="top"/>
            <xsl:if test="//container[@type='folder']">
              <col width="7%" align="left" valign="top"/>
            </xsl:if>
            <col width="86%"/>
            <!-- process container c01s -->
            <xsl:apply-templates select="c01/did"/>
          </table>
        </xsl:otherwise>
      </xsl:choose>
    </div>
  </xsl:template>
  
  <xsl:template match="dsc/head">
    <h2><xsl:apply-templates/></h2>
  </xsl:template>


  <xsl:template match="c01/did[not(container)]|c02/did[not(container)]|c03/did[not(container)]">
    <tr>
      <th colspan="3">
        <xsl:apply-templates/>
      </th>
    </tr>
  </xsl:template>
  
  <xsl:template match="did[container/@type='box']">
    <!-- only show box/folder once for the whole page -->
    <xsl:if test="count(../preceding-sibling::node()/did[container]) = 0">
      <tr>
        <th>Box</th>
        <!-- only display folder label if there are folders -->
        <xsl:if test="//container[@type='folder']">
          <th>Folder</th>
        </xsl:if>
      </tr>
    </xsl:if>
    
    <tr>
      <td>
        <xsl:apply-templates select="container[@type='box']"/>
      </td>
      <xsl:if test="//container[@type='folder']">
        <td>
          <xsl:apply-templates select="container[@type='folder']"/>
        </td>
      </xsl:if>
      <td>
        <xsl:apply-templates select="unittitle"/>
      </td>
    </tr>
  </xsl:template>


  <xsl:template match="container|c01[@level='file']/did/unittitle">
    <xsl:apply-templates/>
  </xsl:template>

  <!-- generic templates -->
  <xsl:template match="head">
    <b><xsl:apply-templates/></b>
  </xsl:template>


  <xsl:template match="title">
    <i><xsl:apply-templates/></i>
  </xsl:template>

  <xsl:template match="p">
    <p class="indent">
      <xsl:apply-templates/>
    </p>
  </xsl:template>

  <xsl:template match="bibref">
    <p class="bibref">
      <xsl:apply-templates/>
    </p>
  </xsl:template>


  <!-- summary mode:
       brief display of series & subseries (hits if keyword search)
       -->

  <xsl:template match="dsc/head" mode="summary">
    <xsl:apply-templates select="."/>
  </xsl:template>
	

  <!-- display c0# series -->
  <xsl:template match="c01[@level='series']|c02[@level='subseries']|c03[@level='subseries']">
    <div>
      <xsl:attribute name="class">pagebreak <xsl:value-of select="@level"/></xsl:attribute>
      
      <h2>
        <xsl:apply-templates select="did/unitid"/>
        <br/>      
        <xsl:apply-templates select="did/unittitle"/>
        <xsl:text> </xsl:text>
        <xsl:apply-templates select="did/unitdate"/>
        <br/>
        <xsl:value-of select="did/physdesc"/>          
      </h2>

      <xsl:apply-templates select="bioghist"/>
      <xsl:apply-templates select="scopecontent"/>
      <xsl:apply-templates select="arrangement"/>
      <xsl:apply-templates select="otherfindaid"/>
      <xsl:apply-templates select="accessrestrict"/>
      <xsl:apply-templates select="userestrict"/>
      <xsl:apply-templates select="altformavail"/>
      <xsl:apply-templates select="originalsloc"/>
      <xsl:apply-templates select="bibliography"/>

      <xsl:choose>
         <xsl:when test="(c02[@level='subseries'] or c03[@level='subseries']) and $mode != 'full'">
           <xsl:apply-templates select="c02|c03" mode="summary"/>
         </xsl:when> 
         <xsl:when test="(c02[@level='subseries'] or c03[@level='subseries']) and $mode = 'full'">
           <xsl:apply-templates select="c02|c03"/>
         </xsl:when> 
      <!-- otherwise, display in tables -->
      <xsl:otherwise> 
        <table width="100%">
          <col width="7%" align="left" valign="top"/>
          <col width="7%" align="left" valign="top"/>
          <col width="86%" align="left" valign="top"/>
          <!-- process sub-container (only one level down) -->
          <xsl:apply-templates select="c02[@level='file']|c03[@level='file']|c04[@level='file']"/>
        </table>
      </xsl:otherwise>
    </xsl:choose> 
    </div>
  </xsl:template>


</xsl:stylesheet>  
