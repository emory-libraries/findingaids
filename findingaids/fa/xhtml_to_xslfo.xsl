<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:fo="http://www.w3.org/1999/XSL/Format"
  version="1.0">

  <xsl:output method="xml"/>

  <xsl:param name="STATIC_ROOT" />
  <xsl:param name="STATIC_URL" />
  <xsl:param name="link_color" value="blue" />

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

      <!-- generate bookmarks -->
      <fo:bookmark-tree>
        <xsl:apply-templates select="//h1[a/@name]" mode="bookmark"/>
      </fo:bookmark-tree>

      <fo:page-sequence master-reference="all-pages">

        <!-- display div with id 'header' at top of all pages after the first -->
        <fo:static-content flow-name="header">
           <fo:block font-family="any" left="0in" font-size="10pt" margin-left="0.25in">
            <xsl:apply-templates select="//div[@id='header']" mode="header-footer"/>
           </fo:block>
      </fo:static-content>

        <!-- display div with id 'firstpage-footer' at the foot of the first page -->
      <fo:static-content flow-name="firstpage-footer">
        <fo:block text-align="start" font-family="any" font-style="italic"
          font-size="10pt" margin-left="0.5in" margin-right="0.5in">
            <xsl:apply-templates select="//div[@id='firstpage-footer']" mode="header-footer"/>
        </fo:block>
      </fo:static-content>

      <!-- display the page number at the bottom of all pages after the first -->
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

 <!-- ignore 'special' (header/footer) sections during normal text output -->
 <xsl:template match="div[@id='header'] | div[@id='footer'] | div[@id='firstpage-footer']"/>

 <xsl:template match="div[@id='header'] | div[@id='footer'] | div[@id='firstpage-footer']"
   mode="header-footer">
    <xsl:apply-templates/>
 </xsl:template>

 <xsl:template match="h1[a/@name]|h2[a/@name]" mode="bookmark">
   <fo:bookmark>
     <xsl:attribute name="internal-destination"><xsl:value-of select="a/@name"/></xsl:attribute>
     <fo:bookmark-title><xsl:value-of select="normalize-space(a)"/></fo:bookmark-title>
     <xsl:choose>
       <xsl:when test="local-name(.) = 'h1'">
         <!-- include top-level series -->
         <xsl:apply-templates select="//h2[a/@name][@class='series']" mode="bookmark"/>
       </xsl:when>
     </xsl:choose>
   </fo:bookmark>
 </xsl:template>


 <xsl:template match="div[@id='title']|h1">
   <fo:block font-size="18pt" font-family="any" text-align="center"
     space-after="30pt" font-weight="bold">
     <xsl:apply-templates/>
   </fo:block>
 </xsl:template>

 <!-- don't use normal h2 formatting for title -->
 <xsl:template match="div[@id='title']/h2">
   <xsl:apply-templates/>
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
     <xsl:if test="contains(@class, 'pagebreak') or contains(@class, 'nextpage')">
       <xsl:attribute name="break-before">page</xsl:attribute>
     </xsl:if>
     <xsl:apply-templates/>
   </fo:block>
 </xsl:template>

 <xsl:template match="div[@id='publication_statement']">
   <fo:block font-size="14pt" font-family="any" text-align="center"
     space-after.optimum="20pt">
     <xsl:apply-templates/>
   </fo:block>
 </xsl:template>

 <xsl:template match="div[@id='publication_statement']/h3|div[@id='publication_statement']/h4">
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
       <xsl:when test="@class = 'c02'">
         <xsl:attribute name="text-indent">10pt</xsl:attribute>
       </xsl:when>
       <xsl:when test="@class = 'c03'">
         <xsl:attribute name="text-indent">20pt</xsl:attribute>
       </xsl:when>
       <xsl:when test="@class = 'no-margin' or ancestor::div/@class = 'no-margin'">
         <xsl:attribute name="space-before">0pt</xsl:attribute>
         <xsl:attribute name="space-after">0pt</xsl:attribute>
       </xsl:when>
       <xsl:otherwise>
         <xsl:attribute name="space-after">5pt</xsl:attribute>
       </xsl:otherwise>
     </xsl:choose>
     <xsl:apply-templates/>
   </fo:block>
 </xsl:template>

 <xsl:template match="i | node()[@class='ead-italic'] | node()[@class='ead-title']">
   <fo:inline font-style="italic">
     <xsl:apply-templates/>
   </fo:inline>
 </xsl:template>

 <xsl:template match="b | node()[@class='ead-bold']">
   <fo:inline font-weight="bold">
     <xsl:apply-templates/>
   </fo:inline>
 </xsl:template>

 <xsl:template match="table">
   <fo:table>
     <xsl:if test="not(./@id) or ./@id != 'descriptivesummary'">
       <xsl:attribute name="margin-top">12pt</xsl:attribute>
     </xsl:if>
     <!-- fop complains about table-layout auto; auto is treated as fixed, width=100% -->
     <xsl:attribute name="table-layout">fixed</xsl:attribute>
     <!-- if table has a width, use that; otherwise, specify 100% -->
     <xsl:choose>
       <xsl:when test="@width">
         <xsl:attribute name="width"><xsl:value-of select="@width"/></xsl:attribute>
       </xsl:when>
       <xsl:otherwise>
         <xsl:attribute name="width">100%</xsl:attribute>
       </xsl:otherwise>
     </xsl:choose>
     <!-- NOTE: for apache fop, columns must be specified; html should specify cols with % widths -->
     <xsl:apply-templates select="col"/>
     <xsl:choose>
     <xsl:when test="tr[th and not(td) and position() = 1] and
            ./@class != 'box-folder'"> <!-- special case: suppress running header for box/folder/contents -->
       <fo:table-header>
         <xsl:apply-templates select="tr[th and not(td) and position() = 1]"/>
       </fo:table-header>
       <fo:table-body>
         <xsl:apply-templates select="tr[position() != 1]"/>
       </fo:table-body>
     </xsl:when>
     <xsl:otherwise>
       <fo:table-body>
         <xsl:apply-templates select="tr"/>
       </fo:table-body>
     </xsl:otherwise>
     </xsl:choose>
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

 <!-- NOTE: setting keep-together="always" implicitly sets
      keep-together.within-line="always" as of FOP 0.94, which keeps table contents from wrapping.
      Hopefully a keep-together strength of 5 is sufficient for our needs.  -->
 <xsl:template match="tr">
   <fo:table-row> <!-- keep-together="5"> -->
     <xsl:apply-templates/>
   </fo:table-row>
 </xsl:template>

<xsl:template match="tr[th]">
  <fo:table-row keep-together="5" keep-with-next="always"> <!-- space-after="5pt"> -->
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
       <xsl:if test="(ancestor::table/@class = 'box-folder' or @class='bf' or @class='content')
                and name() = 'th'">
         <xsl:attribute name="font-size">10pt</xsl:attribute>
       </xsl:if>
       <xsl:if test="name() = 'th'">
         <xsl:attribute name="font-weight">bold</xsl:attribute>
       </xsl:if>
       <!-- section headings within container list should be bold & have extra space -->
       <xsl:if test="parent::tr/@class = 'section' or @class = 'section'">
         <xsl:attribute name="font-weight">bold</xsl:attribute>
         <!-- add space if not first row & not *immediately* following another section row -->
         <xsl:if test="parent::tr/preceding-sibling::tr or
                            parent::tr/preceding-sibling::tr[1][not(@class = 'section')]">
            <xsl:attribute name="padding-before">12pt</xsl:attribute>
         </xsl:if>
       </xsl:if>
       <xsl:if test="@class = 'content'">
         <!-- indent secondary lines of content description -->
         <xsl:attribute name="margin-left">20pt</xsl:attribute>
         <xsl:attribute name="text-indent">-10pt</xsl:attribute>
       </xsl:if>
       <xsl:apply-templates select="@align|@style"/>    <!-- handle text alignment -->
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

 <xsl:template match="a[@href]">
   <fo:basic-link text-decoration="underline">
    <xsl:attribute name="color"><xsl:value-of select="$link_color" /></xsl:attribute>
     <xsl:choose>
       <xsl:when test="starts-with(@href, '#')">
         <xsl:attribute name="internal-destination"><xsl:value-of select="substring-after(@href, '#')"/></xsl:attribute>
       </xsl:when>
       <xsl:otherwise>
          <xsl:attribute name="external-destination">url('<xsl:value-of select="@href"/>')</xsl:attribute>
       </xsl:otherwise>
     </xsl:choose>
     <xsl:apply-templates/>
   </fo:basic-link>
 </xsl:template>

<xsl:template match="@align|@style">
  <xsl:choose>
    <xsl:when test=".='right' or contains(., 'text-align:right')">
      <xsl:attribute name="text-align">end</xsl:attribute>
    </xsl:when>
    <xsl:when test=".='left' or contains(., 'text-align:left')">
      <xsl:attribute name="text-align">start</xsl:attribute>
    </xsl:when>
  </xsl:choose>
</xsl:template>

 <xsl:template match="a[@name]">
   <fo:inline>
     <xsl:attribute name="id"><xsl:value-of select="@name"/></xsl:attribute>
     <xsl:apply-templates/>
   </fo:inline>
 </xsl:template>

 <xsl:template match="style"/>

 <xsl:template match="img">
  <fo:external-graphic>
    <xsl:attribute name="src">file:<xsl:value-of select="concat($STATIC_ROOT, substring-after(@src, $STATIC_URL))"/></xsl:attribute>
  </fo:external-graphic>
</xsl:template>

<!-- special case: digital materials banner -->
<xsl:template match="div[@id='digital-materials']">
   <xsl:variable name="banner_width">5</xsl:variable>

  <fo:block-container width="5in" height="0.6in" background-color="#002878" color="white"
    margin="auto">
    <xsl:attribute name="width"><xsl:value-of select="concat($banner_width, 'in')"/></xsl:attribute>
    <!-- calculate indent relative to page width so banner is centered -->
    <xsl:attribute name="start-indent"><xsl:value-of select="concat(($pagewidth - $banner_width) div 2, 'in')"/></xsl:attribute>
    <!-- NOTE: requires extra layout work here because fop doesn't support float -->
    <fo:block-container position="absolute" top="3px" left="15px" width="0.5in" start-indent="0px">
      <fo:block>
        <xsl:apply-templates select="img"/>
      </fo:block>
    </fo:block-container>
    <fo:block-container position="absolute" top="5px" left="75px" start-indent="0px">
       <fo:block font-size="14pt">
         <xsl:apply-templates select="p[1]"/>
       </fo:block>
       <fo:block font-size="12pt">
          <xsl:apply-templates select="p[2]"/>
        </fo:block>
    </fo:block-container>
  </fo:block-container>
</xsl:template>

</xsl:stylesheet>