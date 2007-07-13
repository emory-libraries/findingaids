<?xml version="1.0"?>
<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
  xmlns:fo="http://www.w3.org/1999/XSL/Format">
  
  <xsl:output indent="yes"/>

  <!-- strings for translating case -->
  <xsl:variable name="lowercase" select="'abcdefghijklmnopqrstuvwxyz'"/>
  <xsl:variable name="uppercase" select="'ABCDEFGHIJKLMNOPQRSTUVWXYZ'"/>
  
  <xsl:template match="/">
    <fo:root xmlns:fo="http://www.w3.org/1999/XSL/Format">
      
      <fo:layout-master-set>
        
        <!-- first page (no header) -->
        <fo:simple-page-master master-name="first"
          page-height="11in" 
          page-width="8.5in"
          margin-top="0.2in" 
          margin-bottom="0.5in"
          margin-left="0.5in" 
          margin-right="0.5in">
          <fo:region-before extent="1.0in"/>
          <fo:region-body margin-bottom="0.7in" 
            column-gap="0.25in" 
            margin-left="0.5in" 
            margin-right="0.5in" 
            margin-top="0.5in"/>
          <fo:region-after extent="0.5in"/>
        </fo:simple-page-master>

        <fo:simple-page-master master-name="basic"
          page-height="11in" 
          page-width="8.5in"
          margin-top="0.2in" 
          margin-bottom="0.5in"
          margin-left="0.5in" 
          margin-right="0.5in">
          <!-- named header region; to keep from displaying on first page -->
          <fo:region-before extent="1.0in" region-name="header"/>
          <fo:region-body margin-bottom="0.7in" 
            column-gap="0.25in" 
            margin-left="0.5in" 
            margin-right="0.5in" 
            margin-top="0.5in"/>
          <fo:region-after extent="0.5in"/>
        </fo:simple-page-master>
        
        <!-- one first page, followed by as many basic pages as necessary -->
        <fo:page-sequence-master master-name="all-pages">
          <fo:single-page-master-reference master-reference="first"/>
          <fo:repeatable-page-master-reference master-reference="basic"/>
        </fo:page-sequence-master>
        
      </fo:layout-master-set> 	
      
      <fo:page-sequence master-reference="all-pages">

        <fo:static-content flow-name="header">
          <fo:table font-family="any" left="0in" right="0in"
            margin-left="0.5in" margin-right="0.5in">
            <fo:table-column column-width="4in"/>
            <fo:table-column column-width="3.5in"/>
            <fo:table-body> 
            <fo:table-row>
              <fo:table-cell>
                <fo:block text-align="start">
                  <xsl:value-of select="/ead/eadheader/filedesc/titlestmt/titleproper"/>
                </fo:block>
              </fo:table-cell>
              <fo:table-cell>
                <fo:block text-align="end">
                  <xsl:value-of select="/ead/archdesc/did/unitid"/>
                </fo:block>
              </fo:table-cell>
            </fo:table-row>
          </fo:table-body>
        </fo:table>
        
      </fo:static-content>
        
        <fo:static-content flow-name="xsl-region-after">
          <fo:block text-align="center" font-family="any">
            <fo:page-number/>
          </fo:block>
        </fo:static-content>
        
        <fo:flow flow-name="xsl-region-body">
          
          <fo:block font-family="any">
            <xsl:apply-templates/>
          </fo:block>		  
          
        </fo:flow>
        
      </fo:page-sequence>	
    
    </fo:root>
  </xsl:template>


  <xsl:template match="text()">
    <xsl:value-of select="."/>
  </xsl:template>

  <!-- <xsl:template match="*|node()" priority="-1">
   <fo:block>
     <xsl:value-of select="local-name()"/> : <xsl:apply-templates/>
   </fo:block>
 </xsl:template> -->


 <xsl:template match="eadheader">
   <xsl:apply-templates/>
 </xsl:template>

 <xsl:template match="titleproper">
   <fo:block font-size="22pt" font-family="any" text-align="center" line-height="30pt" space-after.optimum="40pt">
     <xsl:apply-templates/>
   </fo:block>
 </xsl:template>

 <!-- templates to ignore for now -->
 <xsl:template match="eadid|author|publicationstmt/date|profiledesc"/>

 <xsl:template match="publicationstmt">
   <fo:block font-size="12pt" font-family="any" text-align="center" line-height="16pt" space-after.optimum="20pt"
	font-weight="bold">
     <xsl:apply-templates/>
   </fo:block>
 </xsl:template>

 <xsl:template match="publisher">
   <fo:block space-after.optimum="10pt">
     <xsl:apply-templates/>
   </fo:block>
 </xsl:template>

 <xsl:template match="addressline">
   <fo:block>
     <xsl:apply-templates/>
   </fo:block>
 </xsl:template>
 
 <xsl:template match="archdesc[@level='collection']">
   <xsl:apply-templates select="did"/>

   <fo:block font-size="12pt" font-family="any" text-align="start" line-height="16pt" space-after.optimum="10pt"
	font-weight="bold">Administrative Information</fo:block>
   <fo:block font-size="10pt" border-bottom-color="grey" border-bottom-style="solid" border-bottom-width="1px">
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
   </fo:block>

   <fo:block font-size="12pt" font-family="any" text-align="start" line-height="16pt" space-after.optimum="10pt"
	space-before.optimum="10pt" font-weight="bold">Collection Description</fo:block>
   <fo:block font-size="10pt" border-bottom-color="grey" border-bottom-style="solid" border-bottom-width="1px" >
     <!-- display the following fields, in this specific order -->
     <xsl:apply-templates select="bioghist"/>
     <xsl:apply-templates select="scopecontent"/>
     <xsl:apply-templates select="arrangement"/>
     <xsl:apply-templates select="otherfindaid"/>
   </fo:block>

   <xsl:apply-templates select="controlaccess"/>     

   <xsl:apply-templates select="//dsc"/>     

 </xsl:template>

 <xsl:template match="archdesc/did">
   <fo:block font-size="12pt" font-family="any" text-align="start" line-height="16pt" space-after.optimum="10pt"
	font-weight="bold">Descriptive Summary</fo:block>

   <fo:block font-size="10pt" space-after.optimum="10pt"
   border-bottom-color="grey" border-bottom-style="solid" border-bottom-width="1px">
     <fo:table>
       <fo:table-column column-width="1.5in"/>
       <fo:table-column column-width="4.5in"/>
       <fo:table-body> 
         <xsl:apply-templates/>
       </fo:table-body>
     </fo:table>
   </fo:block>

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
    
  <fo:table-row>
    <fo:table-cell> 
      <fo:block font-weight="bold">
        <xsl:value-of select="$label"/>
      </fo:block>
    </fo:table-cell>
    <fo:table-cell> 
      <fo:block>
        <xsl:apply-templates/>      
      </fo:block>
    </fo:table-cell>
  </fo:table-row> 
  

</xsl:template>

<!-- set off repository subarea from main -->
<xsl:template match="subarea">
  <xsl:text>, </xsl:text> <xsl:apply-templates/>
</xsl:template>


<xsl:template match="archdesc/*[not(self::did) and not(self::dsc)]">
  <fo:block space-after.optimum="5pt">
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>

<xsl:template match="controlaccess[controlaccess]">
   <fo:block font-size="10pt" border-bottom-color="grey" border-bottom-style="solid" border-bottom-width="1px">
     <xsl:apply-templates/>
   </fo:block>
</xsl:template>

<xsl:template match="controlaccess[controlaccess]/head">
 <fo:block font-size="12pt" font-family="any" text-align="start" line-height="16pt" space-after.optimum="10pt"
   space-before.optimum="10pt" font-weight="bold">
     <xsl:apply-templates/>
   </fo:block>
</xsl:template>

<xsl:template match="controlaccess/controlaccess">
   <fo:block space-after.optimum="10pt">
     <xsl:apply-templates/>
   </fo:block>
</xsl:template>

<xsl:template match="controlaccess/controlaccess/head">
   <fo:block font-weight="bold">
     <xsl:apply-templates/>
   </fo:block>
</xsl:template>

<xsl:template match="controlaccess/controlaccess/*[not(self::head)]">
  <fo:block>
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="dsc">
  <fo:block break-before="page">

        <xsl:choose> 
      <xsl:when test="c01/c02 or c01[@level='series']">
        <!-- when there are series & subseries, do a summary display -->
        <xsl:apply-templates mode="summary"/>

        <!-- then display full info -->
        <xsl:apply-templates select="c01"/>
      </xsl:when> 
      <!-- otherwise, display the full container list -->
      <!-- if there are no c02s then process all c01s with containers. Ignore the c01s that are headings -->
      <xsl:otherwise> 
        <xsl:apply-templates select="head"/>

        <fo:table border-width="1px">
          <fo:table-column column-width="0.5in"/>
          <fo:table-column column-width="0.5in"/>
          <fo:table-column column-width="5in"/>
          <fo:table-body>
            <!-- process container c01s -->
            <xsl:apply-templates select="c01/did"/>
          </fo:table-body>
        </fo:table>

        </xsl:otherwise>
    </xsl:choose> 
  </fo:block>
</xsl:template>

<xsl:template match="dsc/head">
 <fo:block font-size="14pt" font-family="any" text-align="start" line-height="16pt" space-after.optimum="10pt"
   space-before.optimum="10pt" font-weight="bold">
   <xsl:apply-templates/>
   </fo:block>
</xsl:template>


<xsl:template match="c01/did[not(container)]|c02/did[not(container)]|c03/did[not(container)]">
  <fo:table-row>
    <fo:table-cell number-columns-spanned="3">
      <fo:block font-size="12pt" font-family="any" text-align="start" line-height="16pt"
        space-before.optimum="10pt" font-weight="bold">
        <xsl:apply-templates/>
      </fo:block>
    </fo:table-cell>
  </fo:table-row>
</xsl:template>





<xsl:template match="did[container/@type='box']">
  <!-- <xsl:template match="c01[@level='file']/did"> -->
  <!--  <fo:table>
       <fo:table-column column-width="0.5in"/>
       <fo:table-column column-width="0.5in"/>
       <fo:table-column column-width="5in"/>
    <fo:table-body> -->

    <!-- only show box/folder once for the whole page -->
      <xsl:if test="count(../preceding-sibling::node()/did[container]) = 0">
        <fo:table-row>
          <fo:table-cell>
            <fo:block font-weight="bold">Box</fo:block>
          </fo:table-cell>
          <!-- only display folder label if there are folders -->
          <xsl:if test="//container[@type='folder']">
            <fo:table-cell>
              <fo:block font-weight="bold">Folder</fo:block>
            </fo:table-cell>
          </xsl:if>
        </fo:table-row>
      </xsl:if>

      <fo:table-row>
        <fo:table-cell>
          <xsl:apply-templates select="container[@type='box']"/>
        </fo:table-cell>
        <fo:table-cell>
          <xsl:apply-templates select="container[@type='folder']"/>
        </fo:table-cell>
        <fo:table-cell>
          <fo:block>
            <xsl:apply-templates select="unittitle"/>
          </fo:block>
        </fo:table-cell>
      </fo:table-row>
      <!--       </fo:table-body>
  </fo:table>  -->
</xsl:template>


<xsl:template match="container|c01[@level='file']/did/unittitle">
  <fo:block>
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>

   <!-- generic templates -->
<xsl:template match="head">
  <fo:block font-weight="bold">
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>

<xsl:template match="title">
  <fo:inline font-style="italic">
    <xsl:apply-templates/>
  </fo:inline>
</xsl:template>


<xsl:template match="p">
  <fo:block space-after.optimum="5pt">
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


  <!-- summary mode:
       brief display of series & subseries (hits if keyword search)
       -->

  <xsl:template match="dsc/head" mode="summary">
    <xsl:apply-templates select="."/>
  </xsl:template>
	
  <xsl:template match="c01|c02|c03" mode="summary">
    <fo:block text-align-last="justify">      
      <xsl:value-of select="did/unitid"/>
      <xsl:text>. </xsl:text>
      <xsl:value-of select="did/unittitle"/>
      <fo:leader leader-pattern="dots"/>
      <xsl:value-of select="did/physdesc"/>
    </fo:block>


    <!-- if there are subseries, indent to display hierarchy -->
    <xsl:if test="count(c02[@level='subseries']) + count(c03[@level='subseries']) > 0">
      <fo:block margin-left="0.5in">
        <xsl:apply-templates select="c02[@level='subseries']|c03[@level='subseries']" mode="summary"/>
      </fo:block>
    </xsl:if>
  </xsl:template>


  <!-- display c0# series -->
  <xsl:template match="c01[@level='series']|c02[@level='subseries']|c03[@level='subseries']">
      <fo:block font-size="14pt" font-family="any" text-align="start" line-height="16pt" break-before="page"
        space-after.optimum="10pt" font-weight="bold">
        <fo:block>
          <xsl:apply-templates select="did/unitid"/>          
        </fo:block>
        <fo:block>
          <xsl:apply-templates select="did/unittitle"/>
          <xsl:text> </xsl:text>
          <xsl:apply-templates select="did/unitdate"/>
        </fo:block>
        <fo:block>
          <xsl:apply-templates select="did/physdesc"/>          
        </fo:block>
      </fo:block>
    
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
         <xsl:when test="c02[@level='subseries'] or c03[@level='subseries']">
           <xsl:apply-templates select="c02|c03"/>
         </xsl:when> 
      <!-- otherwise, display in tables -->
      <xsl:otherwise> 
        <fo:table>
          <fo:table-column column-width="0.5in"/>
          <fo:table-column column-width="0.5in"/>
          <fo:table-column column-width="5in"/>
          <fo:table-body>
            <!-- process sub-container (only one level down) -->
            <xsl:apply-templates select="c02[@level='file']|c03[@level='file']|c04[@level='file']"/>
          </fo:table-body>
        </fo:table>
      </xsl:otherwise>
    </xsl:choose> 
    
  </xsl:template>


</xsl:stylesheet>  
