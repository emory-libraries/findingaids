<?php 

class taminoConnection {

  // connection parameters
  var $host;
  var $db;
  var $coll;
  // whether or not to display debugging information
  var $debug;
  
  // these variables used internally
  var $base_url;
  var $xmlContent;
  var $xml;
  var $xpath;
  var $xsl_result;
  var $xq_rval;
  var $xq_code;
  var $xq_msg;

  // cursor variables
  var $cursor;
  var $count;
  var $position;

  function taminoConnection($argArray) {
    $this->host = $argArray['host'];
    $this->db = $argArray['db'];
    $this->coll = $argArray['coll'];
    $this->debug = $argArray['debug'];

    $this->base_url = "http://$this->host/tamino/$this->db/$this->coll?";
  }

  // send an xquery to tamino & get xml result
  // returns  tamino error code (0 for success, non-zero for failure)
  function xquery ($query, $position = NULL, $maxdisplay = NULL) {
    $myurl = $this->base_url . "_xquery=$query&_encoding=utf-8";
    if (isset($position) && isset($maxdisplay)) {
      $myurl .= "&_cursor=open&_position=$position&_quantity=$maxdisplay&_sensitive=vague";
    }
    if ($this->debug) {
      print "DEBUG: In function taminoConnection::xquery, url is $myurl.<p>";
    }

    $this->xmlContent = file_get_contents($myurl);

    if ($this->xmlContent) {
      $this->initializeXML();
      if ($this->debug) {
        $this->displayXML();
      }
      
      if (!($this->xq_rval)) {    // tamino Error code (0 = success)
         $this->getCursor();
      } else if ($this->xq_rval == "8306") {
      // invalid cursor position (returned when there are no matches)
        $this->count = $this->position = $this->quantity = 0;
        if ($debug) {
  	  print "DEBUG: Tamino error 8306 = invalid cursor position<br>\n";
        }
      } else if ($this->xq_rval) {
         $this->count = $this->position = $this->quantity = 0;
         print "<p>Error: failed to retrieve contents.<br>";
         print "(Tamino error code $error)</p>";
      }

    } else {
      print "<p><b>Error:</b> unable to access database.</p>";
      $this->xq_rval = -1;
    }

   return $this->xq_rval;
  }


  // send an x-query (xql) to tamino & get xml result
  // returns  tamino error code (0 for success, non-zero for failure)
  // optionally allows for use of xql-style cursor
  function xql ($query, $position = NULL, $maxdisplay = NULL) {
    if ($this->debug) {
      print "DEBUG: In function taminoConnection::xql, query is $query.<p>";
    }
    if (isset($position) && isset($maxdisplay)) {
      $xql = "_xql($position,$maxdisplay)=";
    } else {
      $xql = "_xql=";
    }
    $myurl = $this->base_url . $xql . $query;
    if ($this->debug) {
      print "DEBUG: In function taminoConnection::xql, url is $myurl.<p>";
    }
    $this->xmlContent = file_get_contents($myurl);

    if ($this->xmlContent) {
      $this->initializeXML();
      if ($this->debug) {
        $this->displayXML();
      }
    } else {
      print "<p><b>Error:</b> unable to access database.</p>";
      $this->xq_rval = -1;
    }
    
    return $this->xq_rval;
  }

   // retrieve the cursor & get the total count
   function getXqlCursor () {
     // NOTE: this is an xql style cursor, not xquery
     if ($this->xml) {
       $nl = $this->xpath->query("/ino:response/ino:cursor/@ino:count");
       if ($nl) { $this->count = $nl->item(0)->textContent; }
     } else {
       print "Error! taminoConnection xml variable uninitialized.<br>";
     }
   }

      // retrieve the XQuery style cursor & get the total count
   function getCursor () {
     if ($this->xml) {
       $nl = $this->xpath->query("/ino:response/ino:cursor/ino:current/@ino:position");
       if ($nl) {  $this->position = $nl->item(0)->textContent; }
       $nl = $this->xpath->query("/ino:response/ino:cursor/ino:current/@ino:quantity");
       if ($nl) { $this->quantity = $nl->item(0)->textContent; }

       $total = $this->xml->getElementsByTagName("total");
       if ($total) { $this->count = $total->item(0)->textContent; }
     } else {
       print "Error! taminoConnection xml variable uninitialized.<br>";
     }
   }


   // create a new domDocument with the raw xmlContent, retrieve tamino messages
   function initializeXML () {
    $this->xml = new domDocument();
    $this->xml->loadXML($this->xmlContent);
    if (!$this->xml) {
      print "TaminoConnection::initializeXml error: unable to parse xml content.<br>";
      $this->xq_rval = 0;	// not a tamino error but a dom error
    } else {
     $this->xpath = new domxpath($this->xml);
     // note: query returns a dome node list object
     $nl = $this->xpath->query("/ino:response/ino:message/@ino:returnvalue");
     if ($nl) { $this->xq_rval = $nl->item(0)->textContent; }
     $nl = $this->xpath->query("/ino:response/ino:message/ino:messagetext/@ino:code");
     if ($nl) { $this->xq_code = $nl->item(0)->textContent; }
     $nl =  $this->xpath->query("/ino:response/ino:message/ino:messagetext");
     if ($nl) { $this->xq_msg = $nl->item(0)->textContent; }
     if ($this->debug) {
       print "Tamino return value : $this->xq_rval<br>\n";
       if ($this->xq_code) {
         print "Tamino code : $this->xq_code<br>\n";
       }
       if ($this->xq_msg) {
	 print "Tamino message : $this->xq_msg<br>\n";
       }
     }
    }
   }

   // print out xml (for debugging purposes)
   function displayXML () {
     if ($this->xml) {
       $this->xml->formatOutput = true;
       print "<pre>";
       print htmlentities($this->xml->saveXML());
       print "</pre>";
     }
   }
   
}
