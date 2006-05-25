<?php 

include "taminoConnection.class.php";

class xmlDbConnection {

  // connection parameters
  var $host;
  var $port;
  var $db;
  var $coll;
  var $dbtype; 	// tamino,exist
  // whether or not to display debugging information
  var $debug;
  
  // these variables used internally
  var $xmldb;	// tamino or exist class object
  var $xsl_result;

  // xml/xpath variables - references
  var $xml;
  var $xpath;

  // variables for return codes/messages?

  // cursor variables (needed here?)
  var $cursor;
  var $count;
  var $position;

  // variables for highlighting search terms
  var $begin_hi;
  var $end_hi;


  function xmlDbConnection($argArray) {
    $this->host = $argArray['host'];
    $this->db = $argArray['db'];
    $this->coll = $argArray['coll'];
    $this->debug = $argArray['debug'];

    $this->dbtype = $argArray['dbtype'];
    if ($this->dbtype == "exist") {
      // create an exist object, pass on parameters
      $this->xmldb = new existConnection($argArray);
    } else {	// for backwards compatibility, make tamino default
      // create a tamino object, pass on parameters
     $this->xmldb = new taminoConnection($argArray);
    }

    // xmlDb count is the same as tamino or exist count 
    $this->count =& $this->xmldb->count;
    // xpath just points to tamino xpath object
    $this->xml =& $this->xmldb->xml;
    $this->xpath =& $this->xmldb->xpath;

    // variables for highlighting search terms
    // begin highlighting variables are now defined when needed, according to number of terms
    $this->end_hi = "</span>";
  }

  // send an xquery & get xml result
  function xquery ($query, $position = NULL, $maxdisplay = NULL) {
    // pass along xquery & parameters to specified xml db
    $this->xmldb->xquery($this->encode_xquery($query), $position, $maxdisplay);
  }

  // x-query : should only be in tamino...
  function xql ($query, $position = NULL, $maxdisplay = NULL) {
    // pass along xql & parameters to specified xml db
    $this->xmldb->xql($this->encode_xquery($query), $position, $maxdisplay);
  }

  // retrieve cursor, total count    (xquery cursor is default)
  function getCursor () {
    $this->xmldb->getCursor();
  }

  // explicit xquery cursor - for backwards compatibility
  function getXqueryCursor () {
    $this->xmldb->getCursor();
  }

  // get x-query cursor (for backwards compatibility)
  function getXqlCursor () {
    $this->xmldb->getXqlCursor();
  }

   // transform the database returned xml with a specified stylesheet
   function xslTransform ($xsl_file, $xsl_params = NULL) {
     /* load xsl & xml as DOM documents */
     $xsl = new DomDocument();
     $xsl->load($xsl_file);

     /* create processor & import stylesheet */
     $proc = new XsltProcessor();
     $xsl = $proc->importStylesheet($xsl);
     if ($xsl_params) {
       foreach ($xsl_params as $name => $val) {
         $proc->setParameter(null, $name, $val);
       }
     }
     /* transform the xml document and store the result */
     $this->xsl_result = $proc->transformToDoc($this->xmldb->xml);
   }

   function printResult ($term = NULL) {
     if ($this->xsl_result) {
       if (isset($term[0])) {
         $this->highlightXML($term);
         // this is a bit of a hack: the <span> tags used for
         // highlighting are strings, and not structural xml; this
         // allows them to display properly, rather than with &gt; and
         // &lt; entities
	 //print html_entity_decode($this->xsl_result->saveXML());
	print $this->xsl_result->saveXML();
       } else {
         print $this->xsl_result->saveXML();
       }
     }

   }

   // get the content of an xml node by name when the path is unknown
   function findNode ($name, $node = NULL) {
     // this function is for backwards compatibility... 
     if (isset($this->xpath)) {     // only use the xpath object if it has been defined
       $n = $this->xpath->query("//$name");
       // return only the value of the first one
       if ($n) { $rval = $n->item(0)->textContent; }
     } else {
       $rval =0;
     }
     return $rval;
   }


   // highlight text within the xml structure
   function highlightXML ($term) {
     // if span terms are not defined, define them now
     if (!(isset($this->begin_hi))) { $this->defineHighlight(count($term)); }
     $this->highlight_node($this->xsl_result, $term);
   }

   // recursive function to highlight search terms in xml nodes
   function highlight_node ($n, $term) {
     // build a regular expression of the form /(term1)|(term2)/i 
     $regexp = "/"; 
     for ($i = 0; $term[$i] != ''; $i++) {
       if ($i != 0) { $regexp .= "|"; }
         $regterm[$i] = str_replace("*", "\w*", $term[$i]); 
         $regexp .= "($regterm[$i])";
       }
     $regexp .= "/i";	// end of regular expression

     $children = $n->childNodes;
     foreach ($children as $i => $c) {
       if ($c instanceof domElement) {		
	 $this->highlight_node($c, $term);	// if a generic domElement, recurse 
       } else if ($c instanceof domText) {	// this is a text node; now separate out search terms

         if (preg_match($regexp, $c->nodeValue)) {
           // if the text node matches the search term(s), split it on the search term(s) and return search term(s) also
           $split = preg_split($regexp, $c->nodeValue, -1, PREG_SPLIT_DELIM_CAPTURE | PREG_SPLIT_NO_EMPTY);

           // loop through the array of split text and create text nodes or span elements, as appropriate
           foreach ($split as $s) {
	     if (preg_match($regexp, $s)) {	// if it matches, this is one of the terms to highlight
	       for ($i = 0; $regterm[$i] != ''; $i++) {
	         if (preg_match("/$regterm[$i]/i", $s)) { 	// find which term it matches
                   $newnode = $this->xsl_result->createElement("span", $s);
	           $newnode->setAttribute("class", "term" . ($i+1));	// use term index for span class (begins at 1 instead of 0)
	         }
	       }
             } else {	// text between search terms - regular text node
	       $newnode = $this->xsl_result->createTextNode($s);
	     }
	    // add newly created element (text or span) to parent node, using old text node as reference point
	    $n->insertBefore($newnode, $c);
           }
           // remove the old text node now that we have added all the new pieces
           $n->removeChild($c);
	 }
       }   // end of processing domText element
     }	
   }

   // print out search terms, with highlighting matching that in the text
   function highlightInfo ($term) {
     if (!(isset($this->begin_hi))) { $this->defineHighlight(count($term)); }
     if (isset($term[0])) {
       print "<p align='center'>The following search terms have been highlighted: ";
       for ($i = 0; isset($term[$i]); $i++) {
	 print "&nbsp; " . $this->begin_hi[$i] . "$term[$i]$this->end_hi &nbsp;";
       }
       print "</p>";
     }
   }

   // create <span> tags for highlighting based on number of terms
   function defineHighlight ($num) {
     $this->begin_hi = array();
    // strings for highlighting search terms 
    for ($i = 0; $i < $num; $i++) {
      $this->begin_hi[$i]  = "<span class='term" . ($i + 1) . "'>";
    }
   }


  // convert a readable xquery into a clean url for tamino or exist
  function encode_xquery ($string) {
    // get rid of multiple white spaces
    $string = preg_replace("/\s+/", " ", $string);
    // convert spaces to their hex equivalent
    $string = str_replace(" ", "%20", $string);
    // convert ampersand & # within xquery (e.g., for unicode entities) to hex
    $string = str_replace("&", "%26", $string);
    $string = str_replace("#", "%23", $string);
    return $string;
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
