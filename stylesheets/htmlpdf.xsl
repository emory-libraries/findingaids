<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:fo="http://www.w3.org/1999/XSL/Format"
  version="1.0">

  <xsl:output method="xml"/>

  <!-- width of inner page (content portion), in inches 
       (used to calculate table column sizes)   -->
  <xsl:variable name="pagewidth">6.5</xsl:variable>

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
          <fo:region-body margin-bottom="0.7in" 
            column-gap="0.25in" 
            margin-left="0.5in" 
            margin-right="0.5in" 
            margin-top="0.5in"/>
          <fo:region-before extent="1.0in"/>
          <fo:region-after extent="0.5in"/>
        </fo:simple-page-master>

        <fo:simple-page-master master-name="basic"
          page-height="11in" 
          page-width="8.5in"
          margin-top="0.2in" 
          margin-bottom="0.5in"
          margin-left="0.5in" 
          margin-right="0.5in">
          <fo:region-body margin-bottom="0.7in" 
            column-gap="0.25in" 
            margin-left="0.5in" 
            margin-right="0.5in" 
            margin-top="0.5in"/>
          <!-- named header region; to keep from displaying on first page -->
          <fo:region-before extent="1.0in" region-name="header"/>
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
                  <xsl:value-of select="//div[@id='title']"/>
                </fo:block>
              </fo:table-cell>
              <fo:table-cell>
                <fo:block text-align="end">
                  <xsl:value-of select="//span[@id='unitid']"/>
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

 <xsl:template match="div[@id='title']">
   <fo:block font-size="22pt" font-family="any" text-align="center" line-height="30pt" space-after.optimum="40pt">
     <xsl:apply-templates/>
   </fo:block>
 </xsl:template>


 <xsl:template match="h2">
   <fo:block font-size="14pt" font-family="any" line-height="16pt" space-after.optimum="10pt"
	space-before.optimum="5pt" font-weight="bold" keep-with-next="always">
     <xsl:apply-templates/>
   </fo:block>
 </xsl:template>

 <xsl:template match="h3">
   <fo:block font-size="12pt" font-family="any" line-height="16pt" space-after.optimum="0pt"
	font-weight="bold" keep-with-next="always">
     <xsl:apply-templates/>
   </fo:block>
 </xsl:template>


 <xsl:template match="h4">
   <fo:block space-before.optimum="5pt" keep-with-next="always">
     <xsl:choose>
       <xsl:when test="@class = 'c01' or @class = 'c02' or @class = 'c03'">
       </xsl:when>
       <xsl:otherwise>
         <xsl:attribute name="font-weight">bold</xsl:attribute>
       </xsl:otherwise>
     </xsl:choose>
     <xsl:apply-templates/>
   </fo:block>
 </xsl:template>

 <xsl:template match="div">
   <fo:block>
     <xsl:if test="contains(@class, 'pagebreak')">
       <xsl:attribute name="break-before">page</xsl:attribute>
     </xsl:if>
     <xsl:apply-templates/>
   </fo:block>
 </xsl:template>

 <xsl:template match="div[@id='publicationstmt']">
   <fo:block font-size="12pt" font-family="any" text-align="center" line-height="16pt" space-after.optimum="20pt"
	font-weight="bold">
     <xsl:apply-templates/>
   </fo:block>
 </xsl:template>

<xsl:template match="hr">
  <fo:block border-bottom-color="grey" border-bottom-style="solid"
    border-bottom-width="0.1mm" space-after.optimum="5pt" space-before.optimum="5pt"/>
 </xsl:template> 

 <xsl:template match="p">
   <fo:block>
     <xsl:choose>
       <xsl:when test="@class = 'tight'">
         <xsl:attribute name="space-after.optimum">0pt</xsl:attribute>
       </xsl:when>
       <xsl:when test="@class = 'bibref'">
         <xsl:attribute name="space-before.optimum">5pt</xsl:attribute>
       </xsl:when>
       <xsl:otherwise>
         <xsl:attribute name="space-after.optimum">5pt</xsl:attribute>
       </xsl:otherwise>       
     </xsl:choose>
     <xsl:apply-templates/>
   </fo:block>
 </xsl:template>

 <xsl:template match="i">
   <fo:inline font-style="italic">
     <xsl:apply-templates/>
   </fo:inline>
 </xsl:template>

 <xsl:template match="b">
   <fo:inline font-weight="bold">
     <xsl:apply-templates/>
   </fo:inline>
 </xsl:template>


 <xsl:template match="table">
   <fo:table>
     <!-- FIXME: how to get columns? use table id /class -->
     <xsl:apply-templates select="col"/>
     <fo:table-body>
       <xsl:apply-templates select="tr"/>
     </fo:table-body>
   </fo:table>
 </xsl:template>

 <xsl:template match="table/col">
   <!-- convert percent value into a number xslt can process -->
   <xsl:variable name="p0"><xsl:value-of select="substring-before(@width, '%')"/></xsl:variable>
   <xsl:variable name="pct">
     <xsl:choose>
       <!-- if percent is only 1 digit, add leading zero -->
       <xsl:when test="string-length($p0) = 1">
         <xsl:value-of select="concat('0.0', $p0)"/>
       </xsl:when>
       <xsl:otherwise>
         <xsl:value-of select="concat('0.', $p0)"/>
       </xsl:otherwise>
     </xsl:choose>
   </xsl:variable>

   <!-- calculate column width based on percent of page width -->
   <xsl:variable name="colwidth">
     <xsl:value-of select="$pagewidth * $pct"/>
   </xsl:variable>

   <fo:table-column>
     <xsl:attribute name="column-width"><xsl:value-of select="$colwidth"/>in</xsl:attribute>
   </fo:table-column>
 </xsl:template>

 <xsl:template match="tr">
   <fo:table-row keep-together="always">
     <xsl:apply-templates/>
   </fo:table-row>
 </xsl:template>

 <xsl:template match="td|th">
   <fo:table-cell>
     <xsl:if test="@colspan">
       <xsl:attribute name="number-columns-spanned"><xsl:value-of select="@colspan"/></xsl:attribute>
     </xsl:if>
     <fo:block>
       <xsl:if test="name() = 'th'">
         <xsl:attribute name="font-weight">bold</xsl:attribute>
       </xsl:if>
       <xsl:apply-templates/>
     </fo:block>
   </fo:table-cell>
 </xsl:template>


 <xsl:template match="ul">
   <fo:block margin-left="0.5in">
     <xsl:apply-templates/>
   </fo:block>
 </xsl:template>

 <xsl:template match="br">
   <fo:block/>
 </xsl:template>

</xsl:stylesheet>
