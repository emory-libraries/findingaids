#!/usr/bin/perl
use strict;

my ($taminoDb, $taminoCollection, $inputDir);

# update this for each project
$taminoDb = "BECKCTR";

$inputDir="./xml/tamino";
print "\nLoading files in $inputDir to Tamino database $taminoDb.\n";

print "\nWhat collection in  $taminoDb will you be loading?\n";
$taminoCollection = readline(*STDIN);
chop $taminoCollection;

print " Check for success of javaloader by examining $inputDir/done and $inputDir/errors \n";


open (LOAD, "perl 'tamino-data-load.pl' '-i' '$inputDir' '-d' '$taminoDb' '-c' '$taminoCollection'|");
while (<LOAD>){
    print "$_\n";
}
close (LOAD);

if ($?) {print " More information about the cause  for failure of the javaloader may be found in $inputDir/done and $inputDir/errors \n\n"}
else{print " More information about the results of the javaloader may be found in $inputDir/done and $inputDir/errors \n\n"}

exit;
