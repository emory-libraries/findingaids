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
        
        <fo:simple-page-master master-name="simple"
          page-height="11in" 
          page-width="8.5in"
          margin-top="0.2in" 
          margin-bottom="0.5in"
          margin-left="0.5in" 
          margin-right="0.5in">
          <fo:region-before extent="1.0in"/>
          <fo:region-body margin-bottom="0.7in" 
            column-gap="0.25in" 
            margin-left="1.0in" 
            margin-right="0.2in" 
            margin-top="0.5in"/>
          <fo:region-after extent="0.5in"/>
        </fo:simple-page-master>
        
      </fo:layout-master-set> 	  
      
      <fo:page-sequence master-reference="simple">

        <fo:static-content flow-name="xsl-region-before">
          <fo:block text-align="center">
            <xsl:value-of select="/ead/eadheader/filedesc/titlestmt/titleproper"/>
            <xsl:text> - </xsl:text>
            <xsl:value-of select="/ead/archdesc/did/unitid"/>
          </fo:block>

        </fo:static-content>
        
        <fo:static-content flow-name="xsl-region-after">
          <fo:block text-align="end" font-family="any">
            Page <fo:page-number/>
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
     <xsl:apply-templates select="acqinfo | accessrestrict | userestrict | prefercite | separatedmaterial"/>     
   </fo:block>

   <fo:block font-size="12pt" font-family="any" text-align="start" line-height="16pt" space-after.optimum="10pt"
	space-before.optimum="10pt" font-weight="bold">Collection Description</fo:block>
   <fo:block font-size="10pt" border-bottom-color="grey" border-bottom-style="solid" border-bottom-width="1px" >
     <xsl:apply-templates select="bioghist | scopecontent"/>     
   </fo:block>

   <xsl:apply-templates select="controlaccess"/>     

   <xsl:apply-templates select="dsc"/>     

 </xsl:template>

 <xsl:template match="archdesc/did">
   <fo:block font-size="12pt" font-family="any" text-align="start" line-height="16pt" space-after.optimum="10pt"
	font-weight="bold">Descriptive Summary</fo:block>

   <fo:block font-size="10pt" border-bottom-color="grey" border-bottom-style="solid" border-bottom-width="1px"
	space-after.optimum="10pt">
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


<xsl:template match="archdesc/*[not(self::did)]">
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


<xsl:template match="dsc/head">
 <fo:block font-size="12pt" font-family="any" text-align="start" line-height="16pt" space-after.optimum="10pt"
   space-before.optimum="10pt" font-weight="bold">
     <xsl:apply-templates/>
   </fo:block>
</xsl:template>



<xsl:template match="c01[@level='file']/did">
  <fo:table>
       <fo:table-column column-width="0.5in"/>
       <fo:table-column column-width="0.5in"/>
       <fo:table-column column-width="5in"/>
    <fo:table-body>

      <xsl:if test="count(../preceding-sibling::node()/did) = 0">
        <fo:table-row>
          <fo:table-cell>
            <fo:block font-weight="bold">Box</fo:block>
          </fo:table-cell>
          <fo:table-cell>
            <fo:block font-weight="bold">Folder</fo:block>
          </fo:table-cell>
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
          <xsl:apply-templates select="unittitle"/>
        </fo:table-cell>
      </fo:table-row>
    </fo:table-body>
  </fo:table>
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


<xsl:template match="p">
  <fo:block>
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


</xsl:stylesheet>  
