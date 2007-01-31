#!/usr/bin/perl

## A simple perl script to consistently formatted text (saved from MS
## Word files) into index entries for EAD xml
## input format should look like this:
##	
## NAME
## ref
##
## resulting output is formatted like this:
##
## <indexentry>
##   <persname>NAME</persname>
##   <ptrgrp>
##     <ref>ref</ref>
##   </ptrgrp>
## </indexentry>


use Carp;
use strict;
use File::Basename;

my($input, $output, @infiles, $state, $usage);

$usage = "Usage:
  indexentry.pl
  indexentry.pl -i inputdir -o outputdir
  indexentry.pl -h	

  indexentry.pl takes as input consistently formatted text files and
  outputs xml in EAD indexentry format.  If input and output
  directories are not specified, the script will prompt the user to
  supply them.

   Options:
	-i	Input directory (processes all .txt files)
	-o	Output directory
	-h	Display usage information
		No options: prompts user for input & output directories

";

for (my $i=0; $i<=$#ARGV; $i++){
    if ($ARGV[$i] =~ /-i/) { $i++; $input = $ARGV[$i]}
    if ($ARGV[$i] =~ /-o/) { $i++; $output = $ARGV[$i]}
    if ($ARGV[$i] =~ /-h/) { print $usage; exit; }
}

if (!$input){
  print "\nWhat directory of files do you want to translate? (enter the directory name)\n";
  $input = readline(*STDIN);
  chomp($input);
}

if (!$output){
  print "\nWhat directory do you want to store the xml output?\n";
  $output = readline(*STDIN);
  chop $output;
}
eval {-d $output} || confess ("Output directory $output is not writable");

opendir (DIR, $input) || die "Couldn't open input directory $input: $!";
@infiles = grep { !/^\./ && /\.txt$/ && -f "$input/$_" } readdir(DIR);
closedir DIR;

my ($f, $basename);

foreach $f (@infiles){
  $basename = basename($f,".txt");     # get the basename of the file

  open(IN, "$input/$f") || die "Couldn't open $input/$f: $!";
  open(OUT, ">$output/$basename.xml");

  $state = "start";
  while(<IN>) {
    chomp($_);
    # blank line - next non-blank line begins a new index entry
    if ($_ =~ m/^\s*$/) {
      # if previous mode was ref, close the loast indexentry
      if ($state eq "ref") {
	print OUT "  </ptrgrp>\n</indexentry>\n\n";
      }
      $state = "start";
      next;
    }
    if ($state eq "start") {
      # first content line after a blank line
      print OUT "<indexentry>\n  <name>$_</name>\n  <ptrgrp>\n";
      # all subsequent non-blank lines are refs
      $state = "ref";
    } elsif ($state eq "ref") {
      print OUT "    <ref>$_</ref>\n";
      $state = "ref";
    }
  }

  close(IN);
  close(OUT);

  print "Finished processing $output/$basename.xml\n";
}

exit;


