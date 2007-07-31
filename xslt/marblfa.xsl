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


        </div>

        <!--start content-->
        <div id="content">
          <!--          <xsl:apply-templates select="//results/ead/eadheader/filedesc/titlestmt"/>-->
          <xsl:apply-templates select="//results/ead"/>		
        </div>
        
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- don't display revision descriptions (Harry Ransom) -->
  <xsl:template match="revisiondesc"/>

  <xsl:template match="titlestmt">
    <div id="title">
      <xsl:if test="$mode != 'full'">
        <!-- print link 
             (kind of a hack: inside title div to float above title bar lined up at the right)
             -->
        <div id="printable">
          <a>
            <xsl:attribute name="onclick">javascript:pdfnotify('pdf.php?id=<xsl:value-of select="//ead/@id"/>')</xsl:attribute>
            <xsl:attribute name="href">pdf.php?id=<xsl:value-of select="//ead/@id"/></xsl:attribute>
            Print finding aid (PDF)
          </a>
        </div>
      </xsl:if>

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


  <xsl:template match="publicationstmt">
    <div id="publicationstmt">
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <xsl:template match="publicationstmt/publisher">
    <h3><xsl:apply-templates/></h3>
  </xsl:template>

  <xsl:template match="publicationstmt/address">
    <!--    <h4><xsl:apply-templates/></h4> -->
    <h3><xsl:apply-templates/></h3>
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
     <xsl:apply-templates select=".//accessrestrict"/>
     <xsl:apply-templates select=".//userestrict"/>
     <xsl:apply-templates select=".//altformavail"/>
     <xsl:apply-templates select=".//originalsloc"/>
     <xsl:apply-templates select=".//relatedmaterial"/>
     <xsl:apply-templates select=".//separatedmaterial"/>
     <xsl:apply-templates select=".//acqinfo"/>
     <xsl:apply-templates select=".//custodhist"/>
     <xsl:apply-templates select=".//prefercite"/>

     <!-- Note: Wake Forest nested these fields under desgrp;
          using .// to pick up these fields anywhere under this node -->
     
     <xsl:if test="bioghist or bibliography or scopecontent or arrangement or otherfindaid">
     <hr/>
       <xsl:element name="h2">
         <a>
           <xsl:attribute name="name">collectionDesc</xsl:attribute>
           Collection Description
         </a>
       </xsl:element>
       <!-- display the following fields, in this specific order -->
       <xsl:apply-templates select="bioghist"/>
       <xsl:apply-templates select="bibliography"/>
       <xsl:apply-templates select="scopecontent"/>
       <xsl:apply-templates select="arrangement"/>
       <xsl:apply-templates select="otherfindaid"/>
       
     </xsl:if>
     
     
     <!-- don't display search terms in full/printable (pdf) version -->
     <xsl:if test="$mode != 'full'">
       <xsl:apply-templates select="controlaccess"/>     
     </xsl:if>

     <hr/>
     
     <xsl:apply-templates select="dsc"/>     

     <!-- index is displayed on a separate page in the website view -->
     <xsl:if test="$mode = 'full'">
       <xsl:apply-templates select="index"/>     
     </xsl:if>

     <!-- handle 'odd' similar to index -->
     <xsl:if test="$mode = 'full'"> 
       <xsl:apply-templates select="odd"/>     
     </xsl:if> 
     
   </div>
 </xsl:template>

 <xsl:template match="archdesc/did">
   <hr/>
    <xsl:element name="h2">

      <a>
        <xsl:attribute name="name">descriptiveSummary</xsl:attribute>	
        <xsl:choose>
          <xsl:when test="did/head">
            <xsl:value-of select="did/head"/>
          </xsl:when>
          <xsl:otherwise>
            Descriptive Summary
          </xsl:otherwise>
        </xsl:choose>
      </a>
    </xsl:element>

    <table id="descriptivesummary">
      <col width="20%" align="left" valign="top"/>
      <col width="80%" align="left" valign="top"/>

     <!-- display the following fields, in this specific order -->
      <xsl:apply-templates select="origination"/>
      <xsl:apply-templates select="unittitle"/>
      <xsl:apply-templates select="unitid"/>
      <xsl:apply-templates select="physdesc"/>
      <xsl:apply-templates select="physloc"/>		
      <xsl:apply-templates select="abstract"/>
      <xsl:apply-templates select="langmaterial"/>
    </table>

 </xsl:template>

 <xsl:template match="unittitle/text()">
   <xsl:if test="starts-with(., ' ')">
     <xsl:text> </xsl:text>
   </xsl:if>

   <xsl:value-of select="normalize-space(.)"/>

   <xsl:if test="substring(., string-length(.), 1) = ' '">
     <xsl:text> </xsl:text>
   </xsl:if>

 </xsl:template>

 <xsl:template match="unittitle/title">
   <i><xsl:apply-templates/></i><xsl:text> </xsl:text>
 </xsl:template>


 <!-- don't display repository; redundant information -->
 <xsl:template match="archdesc/did/repository"/>

 <!-- don't display archdesc title separately (already displayed above) -->
 <xsl:template match="archdesc/did/head" priority="1"/>

 <xsl:template match="archdesc/did/*[not(self::hits)]">
   <xsl:variable name="name"><xsl:value-of select="local-name()"/></xsl:variable>
   
   <xsl:variable name="label">
     <xsl:choose>
       <xsl:when test="$name = 'unittitle'">Title:</xsl:when>
       <xsl:when test="$name = 'unitid'">Call Number:</xsl:when>
       <xsl:when test="$name = 'physdesc'">Extent:</xsl:when>
       <xsl:when test="$name = 'physloc'">Location:</xsl:when>
       <xsl:when test="$name = 'origination'">Creator:</xsl:when>
       <xsl:when test="$name = 'langmaterial'">Language:</xsl:when>

       <!-- only display label once when these elements repeat -->
       <xsl:when test="$name = 'physdesc' and preceding-sibling::physdesc"></xsl:when>
       <xsl:when test="$name = 'abstract' and preceding-sibling::abstract"></xsl:when>

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
       <xsl:choose>
         <xsl:when test="$name = 'unitid'">
           <span id="unitid"><xsl:apply-templates/></span>           
         </xsl:when>
         <xsl:otherwise>
           <xsl:apply-templates/>
         </xsl:otherwise>
       </xsl:choose>
     </td>
   </tr>
   
 </xsl:template>

 <!-- add a space before unitdate (bulk date or circa) -->
 <xsl:template match="unitdate">
   <xsl:text> </xsl:text> <xsl:apply-templates/>
 </xsl:template>		
 
 <!-- <xsl:template match="physdesc">
    <xsl:element name="h3">
      <xsl:apply-templates/>
    </xsl:element>
  </xsl:template> -->

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
    <hr/>
    <h2>
      <a name="searchTerms">
        <xsl:apply-templates/>
      </a>
    </h2>
  </xsl:template>

  <!-- sub-level control access headings -->
  <xsl:template match="controlaccess/controlaccess/head">
    <!--    <h4><xsl:apply-templates/></h4> -->
    <h3><xsl:apply-templates/></h3>
  </xsl:template>

  <xsl:template match="controlaccess/persname | controlaccess/famname | controlaccess/title">
    <p class="tight">
      <xsl:apply-templates/>
    </p>
  </xsl:template>

  <xsl:template match="subject | controlaccess/corpname[not(parent::origination)] |  genreform | geogname | occupation">
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
            <xsl:if test="//container[@type='folder' or @type='Folder']">
              <col width="7%" align="left" valign="top"/>
            </xsl:if>
            <col width="86%"/>
            <!-- process container c01s -->
            <xsl:apply-templates select="c01/did | c01/scopecontent"/>
          </table>
        </xsl:otherwise>
      </xsl:choose>
    </div>
  </xsl:template>
  
  <xsl:template match="dsc/head">
    <h2><xsl:apply-templates/></h2>
  </xsl:template>


  <xsl:template match="c01/did[not(container)]|c02/did[not(container)]|c03/did[not(container)]|c04/did[not(container)]">
    <tr>
      <th colspan="3" class="section">
       <xsl:apply-templates/>
      </th>
    </tr>
  </xsl:template>
  
  <xsl:template match="did[container/@type='box'] | did[container/@type='Box'] 
                       | did[container/@type='volume'] | did[container/@type='Volume']
                       | did[container/@type='Book'] ">
    <!-- only show box/folder once for the whole page -->
     <xsl:if test="count(../preceding-sibling::node()/did[container]) = 0">
                   <!--                    count(../../preceding-sibling::node()//did[container]) = 0">   -->
      <tr class="box-folder">
        <th>Box</th>
        <!-- only display folder label if there are folders -->
        <xsl:if test="//container[@type='folder' or @type='Folder']">
          <th>Folder</th>
        </xsl:if>
        <th class="content">Content</th>
      </tr>
    </xsl:if>
    
    <tr>
      <td>
        <xsl:apply-templates select="container[@type='box' or @type='Box' or @type='Book']"/>
        <xsl:apply-templates select="container[@type='volume' or @type='Volume']"/>
      </td>
      <xsl:if test="//container[@type='folder' or @type='Folder']">
        <td>
          <xsl:apply-templates select="container[@type='folder' or @type='Folder']"/>
        </td>
      </xsl:if>
      <td class="content">
        <xsl:apply-templates select="unittitle"/>
        <xsl:apply-templates select="physdesc|abstract|note"/>
      </td>
    </tr>
  </xsl:template>

  <!-- generic physdesc (not under archdesc) -->
  <xsl:template match="physdesc">
    <xsl:text>, </xsl:text>
    <xsl:apply-templates/>
  </xsl:template>

  <!-- abstract -->
  <xsl:template match="abstract">
    <br/>
    <span class="indent"><xsl:apply-templates/></span>
  </xsl:template>


  <!-- scopecontent within c levels -->
  <xsl:template match="c01/scopecontent | c02/scopecontent | c03/scopecontent | c04/scopecontent">
    <xsl:choose>
      <!-- output as a table row when at item level -->
      <xsl:when test="parent::node()/@level = 'file' or parent::node()/@level='item'">
        <tr>
          <td></td>
          <td></td>	<!-- line up with unittitle, note -->
          <td class="indent"> 
          <xsl:apply-templates/>
        </td>
        </tr>
      </xsl:when>
      <xsl:otherwise>	<!-- not inside a table -->
        <p><xsl:apply-templates/></p>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  
  <xsl:template match="scopecontent/p">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="container|c01[@level='file' or @level='item']/did/unittitle|c01[not(@level)]/did/unittitle">
    <xsl:apply-templates/>
  </xsl:template>

  <!-- generic templates -->
  <xsl:template match="head">
    <h3><xsl:apply-templates/></h3>
  </xsl:template>


  <xsl:template match="title">
    <xsl:choose>
      <!-- if render is doublequote, don't italicize -->
      <xsl:when test="@render = 'doublequote'">
        <xsl:text>"</xsl:text><xsl:apply-templates/><xsl:text>" </xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <i><xsl:apply-templates/></i>
      </xsl:otherwise>
    </xsl:choose>
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
      <xsl:choose>
          <!-- if this node is the first in a subseries and parent does
               not have any content to display, then don't insert pagebreak -->
          <xsl:when test="name() = 'c02'  and not(preceding-sibling::c02) 
                        and (not(../scopecontent) and not(../arrangement) and not(../bioghist))">
        </xsl:when>
          <xsl:when test="name() = 'c03' and not(preceding-sibling::c03)
                          and (not(../scopecontent) and not(../arrangement) and not(../bioghist))">
            <!-- most likely to happen at the c03 level -->
        </xsl:when>
        <xsl:otherwise>
          <!-- default: pagebreak before new series/subseries -->
          <xsl:attribute name="class">pagebreak <xsl:value-of select="@level"/></xsl:attribute>
        </xsl:otherwise>
      </xsl:choose>
      
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
           <!-- make subseries summary display consistent with top-level summary display -->
           <hr/>
           <h2>Description of Subseries</h2>
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
          <xsl:apply-templates select="c02[@level='file' or @level='item'] 
                                       | c03[@level='file' or @level='item']
                                       | c04[@level='file' or @level='item'] 
                                       | c02[not(@level)] | c03[not(@level)] 
                                       | c04[not(@level)]"/>
        </table>
      </xsl:otherwise>
    </xsl:choose> 
    </div>
  </xsl:template>

  <xsl:template match="archdesc/index">
    <hr/> 
    <div>
      <xsl:attribute name="class">pagebreak</xsl:attribute>
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <!-- archdesc is needed to force this template instead of archdesc/* -->
  <xsl:template match="archdesc/odd">
    <hr/> 
    <div class="pagebreak">
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <!-- same level heading as c0# series headings -->
  <xsl:template match="odd/head">
    <h2><xsl:apply-templates/></h2>
  </xsl:template>


  <xsl:template match="index/head">
    <a name="index">
      <h2><xsl:apply-templates/></h2>
    </a>
  </xsl:template>

  <xsl:template match="indexentry">
    <div class="indexentry">
      <xsl:apply-templates/>
    </div>
  </xsl:template>


  <xsl:template match="indexentry/persname|indexentry/name">
    <b><xsl:apply-templates/></b>
  </xsl:template>

  <xsl:template match="indexentry/ptrgrp">
    <ul>
      <xsl:apply-templates/>
    </ul>
  </xsl:template>

  <xsl:template match="indexentry/ptrgrp/ref">
    <li><xsl:apply-templates/></li>
  </xsl:template>


  <xsl:template match="list">
    <ul>
      <xsl:apply-templates/>
    </ul>
  </xsl:template>

  <xsl:template match="item">
    <li><xsl:apply-templates/></li>
  </xsl:template>

  <!-- ignore bold formatting under index -->
  <xsl:template match="odd//emph[@render='bold']">
    <xsl:apply-templates/>
  </xsl:template> 

  <xsl:template match="emph">
    <xsl:choose>
      <xsl:when test="@render = 'doublequote'">
        <xsl:text>"</xsl:text>
        <xsl:apply-templates/>
        <xsl:text>"</xsl:text>
      </xsl:when>
      <xsl:when test="@render = 'bold'">
        <b><xsl:apply-templates/></b>
      </xsl:when>
      <xsl:when test="@render = 'italic'">
        <i><xsl:apply-templates/></i>
      </xsl:when>
    </xsl:choose>
    <xsl:text> </xsl:text>
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


 <!-- highlight keyword matches -->
 <xsl:template match="exist:match">
   <xsl:variable name="txt"><xsl:value-of select="preceding::text()[0]"/></xsl:variable>
   <!-- for some reason, the single space between two matching terms is getting lost; put it back in here. -->
   <xsl:if test="preceding-sibling::exist:match and ($txt = '')">
     <xsl:text> </xsl:text>
   </xsl:if>
   <span class="match"><xsl:apply-templates/></span>
 </xsl:template>


</xsl:stylesheet>  
