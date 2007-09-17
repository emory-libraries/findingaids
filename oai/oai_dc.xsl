<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns="http://www.openarchives.org/OAI/2.0/"
  xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  version="1.0">

  <xsl:output method="xml" omit-xml-declaration="yes"/>
  <xsl:param name="prefix"/>

  <xsl:include href="../xsl/response.xsl"/>

  <!-- note: this variable MUST be set in order to use the setSpec template -->
  <xsl:variable name="config" select="document('./config.xml')" />	 

  <!-- base url for content on website -->
  <xsl:variable name="baseurl">http://marbl.library.emory.edu/FindingAids/content.php?id=</xsl:variable>

  <!-- list identifiers : header information only -->
  <xsl:template match="ead" mode="ListIdentifiers">
    <xsl:call-template name="header"/>
  </xsl:template>


  <!-- get or list records : full information (header & metadata) -->
  <xsl:template match="ead">
    <record>
    <xsl:call-template name="header"/>
    <metadata>
      <oai_dc:dc>
        <dc:identifier><xsl:value-of select="concat($baseurl, @id)"/></dc:identifier>
        <xsl:apply-templates select="eadheader"/>
        <xsl:apply-templates select="archdesc"/>

        <!--        <dc:identifier>PURL</dc:identifier> -->
        <dc:type>Text</dc:type>
        <dc:format>text/xml</dc:format>
      </oai_dc:dc>
    </metadata>
    </record>
  </xsl:template>

  <xsl:template name="header">
    <xsl:element name="header">            
      <xsl:element name="identifier">
        <!-- identifier prefix is passed in as a parameter; should be defined in config file -->
        <xsl:value-of select="concat($prefix, @id)" /> 
      </xsl:element>

      <xsl:element name="datestamp">
        <xsl:value-of select="LastModified" />
      </xsl:element>

      <!-- no sets defined -->      

    </xsl:element>
  </xsl:template>



  <xsl:template match="titlestmt/titleproper">
    <xsl:element name="dc:title">
      <xsl:value-of select="."/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="titlestmt/author">
    <xsl:element name="dc:creator">
      <xsl:value-of select="."/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="editor">
    <xsl:element name="dc:contributor">
      <xsl:value-of select="."/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="publicationstmt/publisher">
    <xsl:element name="dc:publisher">
      <xsl:value-of select="."/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="profiledesc/creation">
    <xsl:apply-templates select="date"/>
  </xsl:template>

  <!-- FIXME: differentiate between the dates? (are they ever different?) -->
  <!--  <xsl:template match="publicationstmt/date|profiledesc/creation/date"> -->
  <xsl:template match="publicationstmt/date">
    <xsl:element name="dc:date">
      <xsl:value-of select="."/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="langusage/language">
    <xsl:element name="dc:language">
      <xsl:value-of select="."/>
    </xsl:element>
  </xsl:template>

  <!-- not in eadheader -->

  <xsl:template match="accessrestrict">
    <xsl:element name="dc:rights">
      <xsl:apply-templates select="p"/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="p">
    <xsl:value-of select="."/>
  </xsl:template>

  <xsl:template match="controlaccess/subject">
    <xsl:element name="dc:subject">
      <xsl:value-of select="."/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="archdesc/did/abstract">
    <xsl:element name="dc:description">
    <xsl:value-of select="."/>
    </xsl:element>
  </xsl:template>


  <!-- by default, don't display text -->
  <xsl:template match="text()"/>

</xsl:stylesheet>
