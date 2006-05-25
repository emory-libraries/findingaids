#!/usr/bin/perl

use LWP::UserAgent;

## a script to delete data from tamino, using tamino's web interface

$usage = "tamino-data-delete.pl -d database -c collection -e element
   -d	tamino database name (e.g., META)
   -c	tamino collection name (e.g, epoet)
   -e   element to delete (e.g., poetgrp)

";

## database: AMPOET, DAAP, POETRY, etc.
## collection: ampoet, daap, irishpoet, yeats, etc.
## element: poetgrp, TEI.2

$debug = 0;

for (my $i=0; $i<=$#ARGV; $i++){
    if ($ARGV[$i] =~ /^-d/) { $i++; $tamino_db = $ARGV[$i]; }
    if ($ARGV[$i] =~ /^-c/) { $i++; $tamino_coll = $ARGV[$i]; }
    if ($ARGV[$i] =~ /^-e/) { $i++; $element = $ARGV[$i]; }
    if ($ARGV[$i] =~ /^-h/) {$help="1";}
#    if ($ARGV[$i] =~ /^-debug/) {$debug="1";}
}

if ($help) {
print $usage;
exit(0);
}


## if settings were not specified on the command line, prompt user

unless ($tamino_db) {
  print "\nFrom which database would you like to delete data?\n";
  $tamino_db = readline(*STDIN);
  chop($tamino_db);
}

unless ($tamino_coll) {
  print "\nFrom which collection in  $tamino_db would you like to delete data?\n";
  $tamino_coll = readline(*STDIN);
  chop($tamino_coll);
}

unless ($element) {
  print "\nWhich element would you like to delete?\n";
  $element = readline(*STDIN);
  chop($element);
}

## definitions
$base_url = "http://vip.library.emory.edu/tamino/$tamino_db/$tamino_coll";

# Create user agent object
$ua = LWP::UserAgent->new;
$ua->agent("CTI Tamino-deletion perlbot/0.1 "); 

$del_url = "$base_url?_Delete=/$element";
if ($debug) { print "delete url is $del_url\n"; }

print "Are you sure? (y/n) ";
$continue = readline(*STDIN);
chop($continue);
if (!($continue =~ m/[yY]/)) {
  exit(0);
}
print "Deleting $element from $tamino_db/$tamino_coll.\n\n";

# Create delete request
my $del_req = HTTP::Request->new(GET => "$del_url");

# Pass request to the user agent and get a response back
my $res = $ua->request($del_req);

# Check the outcome of the response

## if the request fails, quit.
unless ($res->is_success) {
  print "Error: couldn't open url $del_url\n";
  exit(1);
}

$doc = $res->content;
# grab message from the results
$doc =~  m/<ino:message.+>(.*)<\/ino:message\w+>/g;
## messageline or messagetext
print "Tamino response: $1\n\n";






