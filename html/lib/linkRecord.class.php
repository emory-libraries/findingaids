<?php

include_once("dcRecord.class.php");

class linkRecord extends dcRecord {

  // Constructor 
  function linkRecord($argArray, $subjArray = NULL) {
    parent::dcRecord($argArray, $subjArray);	   // call parent constructor

    /* change document root & item names */
    $this->docRoot = "linkCollection";
    $this->docItem = "linkRecord";

  }  // end linkRecord constructor

}
