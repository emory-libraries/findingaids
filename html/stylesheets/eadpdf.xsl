<?xml version="1.0"?>
<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
  xmlns:fo="http://www.w3.org/1999/XSL/Format">
  
  <xsl:output indent="yes"/>
  
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
  
 <xsl:template match="eadheader">
 </xsl:template>

  <xsl:template match="unitid">
    <fo:block font-size="12pt" font-family="any" text-align="end" line-height="16pt" space-after.optimum="80pt">
	  <xsl:apply-templates/>
	</fo:block>
  </xsl:template>
  
  <xsl:template match="corpname">
	<fo:inline font-size="20pt" font-family="any" line-height="24pt">
	  <xsl:apply-templates/>
    </fo:inline>
  </xsl:template>
   
   <xsl:template match="note/p/num">
	<fo:inline font-size="12pt" font-family="any">
	  [<xsl:apply-templates/>]
	  </fo:inline>
  </xsl:template>
   
  <xsl:template match="archdesc/did">
      <xsl:apply-templates select="repository"/>
	  <xsl:apply-templates select="unitid"/>
      <fo:block space-after.optimum="20pt" line-height="24pt">
	      <xsl:apply-templates select="origination/corpname"/>
		  <xsl:apply-templates select="note/p/num"/>
      </fo:block>
	  <fo:block font-size="20pt" font-family="any" line-height="24pt">
	       <xsl:apply-templates select="unittitle"/>, <xsl:apply-templates select="unitdate"/>
	  </fo:block>
	  <xsl:apply-templates select="physdesc"/>
	  <xsl:apply-templates select="physloc"/>
  </xsl:template> 
  
  <xsl:template match="repository">
    <fo:block font-size="12pt" font-family="any" line-height="24pt" text-align="center" space-after.optimum="40pt">
	  <xsl:apply-templates/>
	  </fo:block>
  </xsl:template> 
   
   <xsl:template match="archdesc/did/unittitle">
	<fo:inline font-size="20pt" font-family="any" line-height="24pt">
	  <xsl:apply-templates/> 
	  </fo:inline>
   </xsl:template> 
   
   <xsl:template match="did/unitdate">
    <fo:inline font-size="20pt" font-family="any" line-height="24pt">
	  <xsl:apply-templates/>
	  </fo:inline>
  </xsl:template> 
  
  <xsl:template match="archdesc/did/physdesc">
    <fo:block font-size="12pt" font-family="any" line-height="16pt">
	  <xsl:apply-templates/>
	</fo:block>
  </xsl:template>
  
  <xsl:template match="archdesc/did/physloc">
    <fo:block font-size="12pt" font-family="any" line-height="16pt">
	  <xsl:apply-templates/>
	</fo:block>
  </xsl:template>
  
  <xsl:template match="bioghist">
    <fo:block font-size="12pt" font-family="any" line-height="16pt" space-before.optimum="24pt">
	  <xsl:apply-templates/>
	</fo:block>
  </xsl:template>
  
  <xsl:template match="scopecontent">
    <fo:block font-size="12pt" font-family="any" line-height="16pt" space-before.optimum="24pt">
	  <xsl:apply-templates/>
	</fo:block>
  </xsl:template>
  
  <xsl:template match="arrangement">
    <fo:block font-size="12pt" font-family="any" line-height="16pt" space-before.optimum="12pt">
	  <xsl:apply-templates/>
	</fo:block>
  </xsl:template>
  
  <xsl:template match="add/relatedmaterial">
    <fo:block font-size="12pt" font-family="any" line-height="16pt" space-before.optimum="12pt">
	  <xsl:apply-templates/>
	</fo:block>
  </xsl:template>

  <xsl:template match="add/otherfindaid">
    <fo:block font-size="12pt" font-family="any" line-height="16pt" space-before.optimum="12pt">
	  <xsl:apply-templates/>
	</fo:block>
  </xsl:template>
  
  <xsl:template match="admininfo/accessrestrict">
    <fo:block font-size="12pt" font-family="any" line-height="16pt" space-before.optimum="12pt">
	  <xsl:apply-templates/>
	</fo:block>
  </xsl:template>
  
  <xsl:template match="admininfo/custodhist">
    <fo:block font-size="12pt" font-family="any" line-height="16pt" space-before.optimum="12pt">
	  <xsl:apply-templates/>
	</fo:block>
  </xsl:template>
  
  <xsl:template match="admininfo/prefercite">
    <fo:block font-size="12pt" font-family="any" line-height="16pt" space-before.optimum="12pt">
	  <xsl:apply-templates/>
	</fo:block>
  </xsl:template>
  
  <xsl:template match="admininfo/processinfo">
    <fo:block font-size="12pt" font-family="any" line-height="16pt" space-before.optimum="12pt">
	  <xsl:apply-templates/>
	</fo:block>
  </xsl:template>
  
  <xsl:template match="odd">
    <fo:block font-size="12pt" font-family="any" line-height="16pt" space-before.optimum="12pt">
	  <xsl:apply-templates/>
	</fo:block>
  </xsl:template>
  
    
 <xsl:template match="scopecontent/p">
        <fo:block font-size="12pt" font-family="any" line-height="16pt" space-after.optimum="12pt">
	  <xsl:apply-templates/>
	</fo:block>
  </xsl:template>
  
 <xsl:template match="arrangement/p">
    <fo:block font-size="12pt" font-family="any" line-height="16pt" space-after.optimum="12pt">
	  <xsl:apply-templates/>
	</fo:block>
  </xsl:template>
  
 <xsl:template match="odd/p">
    <fo:block font-size="12pt" font-family="any" line-height="16pt" space-after.optimum="12pt">
	  <xsl:apply-templates/>
	</fo:block>
  </xsl:template>
  
 <xsl:template match="relatedmaterial/p">
    <fo:block font-size="12pt" font-family="any" line-height="16pt" space-after.optimum="12pt">
	  <xsl:apply-templates/>
	</fo:block>
  </xsl:template>
  
 <xsl:template match="otherfindaid/p">
    <fo:block font-size="12pt" font-family="any" line-height="16pt" space-after.optimum="12pt">
	  <xsl:apply-templates/>
	</fo:block>
  </xsl:template>
  
 <xsl:template match="accessrestrict/p">
    <fo:block font-size="12pt" font-family="any" line-height="16pt" space-after.optimum="12pt">
	  <xsl:apply-templates/>
	</fo:block>
  </xsl:template>
  
 <xsl:template match="custodhist/p">
    <fo:block font-size="12pt" font-family="any" line-height="16pt" space-after.optimum="12pt">
	  <xsl:apply-templates/>
	</fo:block>
  </xsl:template>
  
 <xsl:template match="processinfo/p">
    <fo:block font-size="12pt" font-family="any" line-height="16pt" space-after.optimum="12pt">
	  <xsl:apply-templates/>
	</fo:block>
  </xsl:template>
  
 <xsl:template match="prefercite/p">
    <fo:block font-size="12pt" font-family="any" line-height="16pt" space-after.optimum="12pt">
	  <xsl:apply-templates/>
	</fo:block>
  </xsl:template>
  
 <xsl:template match="*[@render='bold']">
    <fo:inline font-weight="bold">
      <xsl:value-of select="."/>
    </fo:inline>
 </xsl:template>
 
 <xsl:template match="*[@render='italic']">
    <fo:inline font-style="italic">
      <xsl:value-of select="."/>
    </fo:inline>
 </xsl:template>
 
 <xsl:template match="*[@render='underline']">
    <fo:inline text-decoration="underline">
      <xsl:value-of select="."/>
    </fo:inline>
 </xsl:template>

 <xsl:template match="dsc[@type='in-depth']">
 <xsl:apply-templates/>
 </xsl:template>	 

 <xsl:template match="dsc[@altrender='5']">
  <fo:table table-layout="fixed" space-after.optimum="12pt">
    <fo:table-column column-width="3cm"/>
	<fo:table-column column-width="3cm"/>
	<fo:table-column column-width="3cm"/>
	<fo:table-column column-width="3cm"/>
	<fo:table-column column-width="3cm"/>
    <xsl:apply-templates/>
  </fo:table>
  </xsl:template>
  
    <xsl:template match="dsc[@altrender='4']">
  <fo:table table-layout="fixed" space-after.optimum="12pt">
    <fo:table-column column-width="3cm"/>
	<fo:table-column column-width="3cm"/>
	<fo:table-column column-width="3cm"/>
	<fo:table-column column-width="6cm"/>
    <xsl:apply-templates/>
  </fo:table>
  </xsl:template>
  
    <xsl:template match="dsc[@altrender='3']">
  <fo:table table-layout="fixed" space-after.optimum="12pt">
    <fo:table-column column-width="3cm"/>
	<fo:table-column column-width="3cm"/>
	<fo:table-column column-width="9cm"/>
	<fo:table-column column-width="1cm"/>
    <xsl:apply-templates/>
  </fo:table>
  </xsl:template>
  
    <xsl:template match="dsc[@altrender='2']">
  <fo:table table-layout="fixed" space-after.optimum="12pt">
    <fo:table-column column-width="3cm"/>
	<fo:table-column column-width="9cm"/>
	<fo:table-column column-width="2cm"/>
	<fo:table-column column-width="1cm"/>
    <xsl:apply-templates/>
  </fo:table>
  </xsl:template>
  
 
 <xsl:template match="archdesc">
<xsl:apply-templates select="did"/>
<xsl:apply-templates select="scopecontent"/>
<xsl:apply-templates select="arrangement"/>
<xsl:apply-templates select="odd[@type='researchnote']"/> 
<xsl:apply-templates select="add/relatedmaterial"/>
<xsl:apply-templates select="otherfindaid"/>
<xsl:apply-templates select="admininfo"/>
<xsl:apply-templates select="odd[@type='gaps']"/> 
<xsl:for-each select="dsc[@type='analyticover']">
    <fo:block font-weight="bold" space-after.optimum="12pt" space-before.optimum="12pt">CONTAINER LIST
    </fo:block>
	<fo:block space-after.optimum="12pt">
    <xsl:apply-templates select="dsc[@type='in-depth']"/>
	</fo:block>
</xsl:for-each>
<xsl:apply-templates select="dsc/note"/>
<xsl:apply-templates select="add/head"/>
<xsl:apply-templates select="add/table"/>
</xsl:template>

<xsl:template match="add/head">
    <fo:block font-size="12pt" font-family="any" line-height="16pt" space-after.optimum="12pt" space-before.optimum="12pt">
	  <xsl:apply-templates/>
	</fo:block>
  </xsl:template>

   <xsl:template match="add/table">
  <fo:table space-after.optimum="12pt">
    <fo:table-column column-width="10cm"/>
	<fo:table-column column-width="3cm"/>
    <xsl:apply-templates/>
  </fo:table>
  </xsl:template>

   <xsl:template match="add/table/tgroup/tbody/row">
    <fo:table-row>
      <xsl:apply-templates/>
    </fo:table-row>
 </xsl:template>

   <xsl:template match="add/table/tgroup/thead/row">
    <fo:table-row>
      <xsl:apply-templates/>
    </fo:table-row>
 </xsl:template>

 <xsl:template match="add/table/tgroup/tbody/row/entry">
    <fo:table-cell>
	<fo:block font-size="12pt" font-family="any">
	      <xsl:apply-templates/>
	</fo:block>
    </fo:table-cell>
 </xsl:template>

  <xsl:template match="add/table/tgroup/thead/row/entry">
    <fo:table-cell>
	<fo:block font-size="12pt" font-family="any">
	      <xsl:apply-templates/>
	</fo:block>
    </fo:table-cell>
 </xsl:template>
 
<xsl:template match="add/table/tgroup/tbody">
	<fo:table-body>
	   <xsl:apply-templates/>
	</fo:table-body>
 </xsl:template>

 <xsl:template match="add/table/tgroup/thead">
	<fo:table-header>
	<fo:table-row space-after.optimum="12pt">
 	   <xsl:apply-templates/>
 	</fo:table-row>
    </fo:table-header>
 </xsl:template>
 

 <xsl:template match="dsc/note">
    
	<fo:block font-size="12pt" font-family="any" line-height="16pt" space-after.optimum="12pt" space-before.optimum="12pt">
	  <xsl:apply-templates/>
	</fo:block>
	
 </xsl:template>
 
  <xsl:template match="dsc/thead/row">
    
	<fo:table-header>
	<fo:table-row space-after.optimum="12pt">
 	   <xsl:apply-templates/>
 	</fo:table-row>
    </fo:table-header>
	
 </xsl:template>
 

 <xsl:template match="dsc/thead/row/entry">
    <fo:table-cell>
	<fo:block font-weight="bold" font-size="12pt" font-family="any">      <xsl:apply-templates/>
	</fo:block>
    </fo:table-cell>
 </xsl:template>
 
<xsl:template match="dsc/c01">
	<fo:table-body>
	   <xsl:apply-templates/>
	</fo:table-body>
 </xsl:template>


 <xsl:template match="dsc/c01/c02/did">
    <fo:table-row space-after.optimum="12pt">
      <xsl:apply-templates/>
    </fo:table-row>
 </xsl:template>
 
  <xsl:template match="dsc/c01/c02/did/container">
    <fo:table-cell>
	<fo:block font-size="12pt" font-family="any">
      <xsl:apply-templates/>
	</fo:block>
    </fo:table-cell>
 </xsl:template>

 <xsl:template match="dsc/c01/c02/did/unittitle">
    <fo:table-cell>
	<fo:block font-size="12pt" font-family="any">
      <xsl:apply-templates/>
	</fo:block>
    </fo:table-cell>
 </xsl:template>
 
 <xsl:template match="dsc/c01/c02/did/unitdate">
    <fo:table-cell>
	<fo:block font-size="12pt" font-family="any">
      <xsl:apply-templates/>
	</fo:block>
    </fo:table-cell>
 </xsl:template>
 
 
 <xsl:template match="dsc/note/p">
   <fo:table-row>
	<fo:table-cell>
	<fo:block font-size="12pt" font-family="any">
      <xsl:apply-templates/>
	</fo:block>
    </fo:table-cell>
	<fo:table-cell>
	</fo:table-cell>
	<fo:table-cell>
	</fo:table-cell>
	<fo:table-cell>
	</fo:table-cell>
	</fo:table-row>
 </xsl:template>
 
 <xsl:template match="dsc/p/note">
   <fo:table-row>
	<fo:table-cell>
	<fo:block font-size="12pt" font-family="any">
      <xsl:apply-templates/>
	</fo:block>
    </fo:table-cell>
	<fo:table-cell>
	</fo:table-cell>
	<fo:table-cell>
	</fo:table-cell>
	<fo:table-cell>
	</fo:table-cell>
	</fo:table-row>
 </xsl:template>
 
</xsl:stylesheet>  
