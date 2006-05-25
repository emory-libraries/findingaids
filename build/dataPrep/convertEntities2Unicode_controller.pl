#!/usr/bin/perl
use Carp;
### This program converts entities to unicode entities.

$i=0;
for (my $i=0; $i<$#ARGV; $i++){
    if ($ARGV[$i] =~ /-i/) { $i++;$inputDirectory = $ARGV[$i]}
    if ($ARGV[$i] =~ /-o/) { $i++;$outputDirectory = $ARGV[$i]}
}
if ($inputDirectory  && $outputDirectory ){}
else {    print "perl converEntites2Unicode_controller.pl -i <input directory> -o <output directory> \n\n";    exit;}

if (opendir (DIR, $inputDirectory)) {}
else{confess ("couldn't open input directory $inputDirectory")}
@inFiles=grep { !/^\./ && -f "$inputDirectory/$_" } readdir(DIR);
closedir DIR;

(-d $outputDirectory || confess ("couldn't open output directory $outputDirectory"));

foreach my $fileName (@inFiles) {
    my ($fileId, $doctype, $xmlFile);
    $_ = $fileName;
    ($fileId)=/(.*)\..*$/;
#    $unicodeFile=$fileId."U.xml";
## don't change filename for wwrp
    $unicodeFile=$fileId.".xml";
    qx{perl convertEntities2Unicode.pl<$inputDirectory/$fileName>$outputDirectory/$unicodeFile};
}
exit;

