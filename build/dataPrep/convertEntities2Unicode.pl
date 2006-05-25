#!/usr/bin/perl
use Carp;
### This program converts entities to unicode entities.

$/ = "";   # enable paragraph mode
$* = 1;	   # enable multi-line patterns

# load definition of entities to replace
require("entity_list.pl");


while (<STDIN>){
  foreach $e (keys (%entity_list)) {
    s/$e/$entity_list{$e}/g;
  }

print $_;
}
exit;
