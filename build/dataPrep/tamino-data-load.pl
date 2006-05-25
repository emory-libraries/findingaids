#!/usr/bin/perl
use Carp;
use File::Spec;  # for portability to Windows
use strict;

my ($inputDir,  $baseDir, $doneDir, $errorDir, @inFiles);
my ($help);
my ($buildArchive, $collection, $classpath, $classpath1, $classpath2, $dtd, $javaMemoryHeapSize);
my ($taminoDb, $taminoCollection);
for (my $i=0; $i<=$#ARGV; $i++){
    if ($ARGV[$i] =~ /^-i/) { $i++;$inputDir = $ARGV[$i]}
    if ($ARGV[$i] =~ /^-d/) { $i++;$taminoDb = $ARGV[$i]}
    if ($ARGV[$i] =~ /^-c/) { $i++;$taminoCollection = $ARGV[$i]}
    if ($ARGV[$i] =~ /^-h/) {$help="1";}
}
    if ($help || !($inputDir) || !($taminoDb) || !($taminoCollection)) { 
	print
	    "\nperl tamino-data-load.pl [-i <input_directory>] -d <tamino_db_name> -c <tamino_collection_name> \n
-i : input directory\n
-d : tamino database name\n
-c : tamino collection name\n
-h : help (this message \n\n";
	exit 9;
    }

# set file separator, '/' or '\' according to operating system
#$operatingSystem = $^O;
#$S='/';
#if ($operatingSystem =~ /win/i){$S="\\"}

#$baseDir=$ENV{'PWD'};

############################################################
# Update following variables for each project
$collection="epoet";
# now set in controller,$inputDir="./build/$collection-HEAD/docs/tamino-data/";
$javaMemoryHeapSize="-Xmx510m"; # increase memory with the mx parameter. must be multiple of 1024k greater than 2mb
############################################################

$inputDir=File::Spec->rel2abs($inputDir);

$_=$inputDir;
($buildArchive)=/(^.*HEAD)/;

my ($operatingSystem, $fileSeparator);
$operatingSystem = $^O;
$fileSeparator=':';
if ($operatingSystem =~ /win/i && !($operatingSystem =~ /darwin/i)){$fileSeparator=";"}


$classpath=File::Spec->catdir($buildArchive,$collection, "dataPrep");
$classpath1=File::Spec->catfile($classpath, "JavaLoader.jar");
$classpath2=File::Spec->catfile($classpath, "xercesTamino.jar");
$classpath="$classpath1$fileSeparator$classpath2$fileSeparator";

$dtd=File::Spec->catfile($buildArchive, "DTD", "tamino-entities.ent");
$dtd=File::Spec->rel2abs($dtd);

$doneDir=File::Spec->catdir($inputDir, "done");
$errorDir=File::Spec->catdir($inputDir, "errors");

if (opendir (DIR, $inputDir)) {}
else{confess ("couldn't open input directory $inputDir")}
@inFiles=grep { !/^\./ && -f "$inputDir/$_" } readdir(DIR);
closedir DIR;

eval{-d $doneDir}||confess("Output directory $doneDir is not writable");
eval{-d $errorDir}||confess("Output directory $errorDir is not writable");

open (LOG, ">load.log") or confess ("Couldn't open load.log");

foreach my $fileName(@inFiles){
    my($errorFile, $inputFile);
    $inputFile=File::Spec->rel2abs("$inputDir/$fileName");
    $errorFile=File::Spec->catfile($errorDir, $fileName."r.err");

    open(STDERR, ">$errorFile") || confess("Can't redirect stderr to $errorFile");
    open(JAVALOADER, "|java $javaMemoryHeapSize -classpath $classpath com.softwareag.tamino.db.tools.loader.TaminoLoad -f $inputFile -u http://vip.library.emory.edu/tamino/$taminoDb/$taminoCollection -d -E $dtd -l -i -p ") or confess ("Can't start java: $!");

    close JAVALOADER or warn $! ? "Error closing java pipe: $!" 
                        : "Exit status $? from java";
    close STDERR;
    if (-z $errorFile) {   #the error file has 0 size, means there is no error :t= tail of the path
#	mv $inputFile $doneDir;  #put the file in the done directory :h= path to the last /
	my $doneFile=File::Spec->catfile($doneDir, $fileName);
	rename ($inputFile, $doneFile);  #put the file in the done directory :h= path to the last /
	print "$fileName loaded\n" ;
	print LOG "$fileName loaded\n"; 
#	rm $errorFile;
	    }
    else{
#this should write the error file and the file to the errors dir and write an error log 
	my $errorFile=File::Spec->catfile($doneDir, $fileName);
	print "load failed for $fileName\n" ;
	print LOG "load failed for $fileName\n";
	mv $inputFile $errorFile;
    }
}
close LOG;

exit ;

