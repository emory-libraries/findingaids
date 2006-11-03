<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:fo="http://www.w3.org/1999/XSL/Format"
  version="1.0">

  <xsl:output method="xml"/>

  <xsl:variable name="disclaimer">
  MARBL provides copies of its finding aids for use only in research
  and private study.  Copies supplied may not be copied for others or
  otherwise distributed without prior consent of MARBL.
  </xsl:variable>

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
          <fo:region-after extent="0.5in" region-name="firstpage-footer"/>
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
          <fo:region-after extent="0.5in" region-name="footer"/>
        </fo:simple-page-master>
        
        <!-- one first page, followed by as many basic pages as necessary -->
        <fo:page-sequence-master master-name="all-pages">
          <fo:single-page-master-reference master-reference="first"/>
          <fo:repeatable-page-master-reference master-reference="basic"/>
        </fo:page-sequence-master>
        
      </fo:layout-master-set> 	
      
      <fo:page-sequence master-reference="all-pages">

        <!-- display collection name / collection # at top of all pages after the first -->
        <fo:static-content flow-name="header">
          <fo:table font-family="any" left="0in" font-size="10pt" margin-left="0.25in">
            <fo:table-column column-width="4.5in"/>
            <fo:table-column column-width="2.5in"/>
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

      <!-- display MARBL disclaimer at the foot of the first page -->
      <fo:static-content flow-name="firstpage-footer">
        <fo:block text-align="start" font-family="any" font-style="italic"
          font-size="10pt" margin-left="0.5in" margin-right="0.5in">
          <xsl:value-of select="normalize-space($disclaimer)"/>
        </fo:block>
      </fo:static-content>

        
      <fo:static-content flow-name="footer">
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
   <fo:block font-size="18pt" font-family="any" text-align="center"
     space-after="30pt" font-weight="bold">
     <xsl:apply-templates/>
   </fo:block>
 </xsl:template>


 <xsl:template match="h2">
   <fo:block font-size="14pt" font-family="any" line-height="16pt"
   space-after="10pt" space-before="10pt"
   font-weight="bold" keep-with-next="always" font-variant="small-caps">
     <xsl:apply-templates/>
   </fo:block>
 </xsl:template>

 <xsl:template match="h3">
   <fo:block font-size="12pt" font-family="any" line-height="16pt"
     space-after="0pt" space-before="10pt"
     font-weight="bold" keep-with-next="always">
     <xsl:apply-templates/>
   </fo:block>
 </xsl:template>


 <xsl:template match="h4">
   <fo:block space-before="5pt" keep-with-next="always">
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
     <xsl:if test="contains(@class, 'indent')">
       <xsl:attribute name="text-indent">10pt</xsl:attribute>
     </xsl:if>
     <xsl:apply-templates/>
   </fo:block>
 </xsl:template>

 <xsl:template match="div[@id='publicationstmt']">
   <fo:block font-size="14pt" font-family="any" text-align="center"
     space-after.optimum="20pt">
     <xsl:apply-templates/>
   </fo:block>
 </xsl:template>

 <xsl:template match="div[@id='publicationstmt']/h3|div[@id='publicationstmt']/h4">
   <!-- should inhert publicationstmt formatting -->
   <fo:block space-after="0pt">
     <xsl:apply-templates/>
   </fo:block>
 </xsl:template>

 <xsl:template match="hr">
   <!-- simulate a double-line by using two blocks with borders -->
   <fo:block border-top-color="black" border-top-style="solid"
     border-top-width="0.1mm" space-before="5pt" space-after="1pt"
     keep-with-next="always"/>
   <fo:block border-bottom-color="black" border-bottom-style="solid"
     border-bottom-width="0.1mm" space-after.optimum="5pt" />
 </xsl:template> 

 <xsl:template match="p">
   <fo:block>
     <xsl:choose>
       <xsl:when test="@class = 'tight'">
         <xsl:attribute name="space-before">0pt</xsl:attribute>
         <xsl:attribute name="space-after">0pt</xsl:attribute>
       </xsl:when>
       <xsl:when test="@class = 'bibref'">
         <xsl:attribute name="space-before">5pt</xsl:attribute>
       </xsl:when>
       <xsl:when test="@class = 'indent'">
         <xsl:attribute name="space-before">0pt</xsl:attribute>
         <xsl:attribute name="space-after">10pt</xsl:attribute>
       </xsl:when>
       <xsl:otherwise>
         <!--         <xsl:attribute name="space-after.optimum">5pt</xsl:attribute> -->
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
     <xsl:if test="@id != 'descriptivesummary'">
       <xsl:attribute name="padding-before">10pt</xsl:attribute>
     </xsl:if>
     <!-- NOTE: for apache fop, columns must be specified; html should specify cols with % widths --> 
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

<xsl:template match="tr[th]">
   <fo:table-row keep-together="always" keep-with-next="always" space-after="5pt">
     <xsl:apply-templates/>
   </fo:table-row>
 </xsl:template>

 <xsl:template match="td|th">
   <fo:table-cell>
     <xsl:if test="@colspan">
       <xsl:attribute name="number-columns-spanned"><xsl:value-of select="@colspan"/></xsl:attribute>
     </xsl:if>
     <fo:block padding-after="2pt">
       <!-- box & folder labels should be smaller -->
       <xsl:if test="../@class = 'box-folder'">
         <xsl:attribute name="font-size">10pt</xsl:attribute>
       </xsl:if>
       <xsl:if test="name() = 'th'">
         <xsl:attribute name="font-weight">bold</xsl:attribute>
       </xsl:if>
       <xsl:if test="@class = 'section'">
         <xsl:attribute name="padding-before">5pt</xsl:attribute>
       </xsl:if>
       <xsl:if test="@class = 'content'">
         <!-- indent secondary lines of content description -->
         <xsl:attribute name="margin-left">20pt</xsl:attribute>
         <xsl:attribute name="text-indent">-10pt</xsl:attribute>
       </xsl:if>
       <xsl:apply-templates/>
     </fo:block>
   </fo:table-cell>
 </xsl:template>

 <xsl:template match="div[@class='indexentry']">
   <fo:block margin-top="10pt">
     <xsl:apply-templates/>
   </fo:block>
 </xsl:template>

 <xsl:template match="ul[li]">
   <fo:list-block>
     <xsl:apply-templates/>
   </fo:list-block>
 </xsl:template>

 <xsl:template match="li">
   <fo:list-item>
     <fo:list-item-label>
       <fo:block/>
     </fo:list-item-label>
     <fo:list-item-body>
       <fo:block>
         <!-- indent any secondary lines -->
         <xsl:attribute name="margin-left">10pt</xsl:attribute>
         <xsl:attribute name="text-indent">-10pt</xsl:attribute>
         <xsl:apply-templates/>
       </fo:block>
     </fo:list-item-body>
   </fo:list-item>
 </xsl:template>

 <xsl:template match="br">
   <fo:block/>
 </xsl:template>

</xsl:stylesheet>