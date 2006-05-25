<?php

include_once("dcCollection.class.php");
include_once("biblRecord.class.php");

class biblCollection extends dcCollection {
  
function initDocFields () {
    /* change document root & item names */
    $this->docRoot = "biblCollection";
    $this->docItem = "biblRecord";
  }



// almost the same as generic version, but using linkRecord instead of dcRecord
function initRecords ($argArray) {
  // initialize id list from Tamino  
  $this->taminoGetIds(); 
  // for each id, create and initialize a dcRecord object
  foreach ($this->ids as $i) {
    $linkargs = $argArray;
    $linkargs["id"] = $i;
    $this->rec[$i] = new biblRecord($linkargs);
    $this->rec[$i]->taminoGetRecord();
  }
}


}
