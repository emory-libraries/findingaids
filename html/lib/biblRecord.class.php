<?php

include_once("dcRecord.class.php");

// bibliographic record class based on Dublin Core
class biblRecord extends dcRecord {

  // Constructor 
  function biblRecord($argArray, $subjArray = NULL) {
    parent::dcRecord($argArray, $subjArray);	   // call parent constructor

    /* change document root & item names */
    $this->docRoot = "biblCollection";
    $this->docItem = "biblRecord";

  }  // end linkRecord constructor


  // print a brief listing of the record
  function printSummary () {
    print "<p>$this->creator. <i>$this->title</i>. ";
    print "$this->publisher : $this->date<br>";
    // What kind of id is useful for a bibligraphy? should it be in the short summary?
    //    print "<font size='-1'>$this->url</font><br>"; 
    print "<b>Description:</b> $this->description<br>";
    print "<font size='-2'>Contributed by: $this->contributor</font><br>";
    print "</p>";
  }

}
