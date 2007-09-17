<?php

// report everything except notices
error_reporting(E_ALL ^ E_NOTICE);

include("../xmldbOAI.class.php");

$oai = new xmldbOAI();
$oai->provide();

?>