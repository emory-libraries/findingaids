#!/usr/bin/perl

## iln_utility.pl : a utility script for the iln xml file
## this script can do any of the following: 
## -entity-name	 fix names of image entities to match image files
## -entity-list	 generate entity list according to entities in file
## -entity-check sanity check on figure entities
## -imgsize	 calculate & insert image sizes (for image viewer)
## -divsize	 calculate & insert div lengths in paragraphs
## -f file	 specify iln file to use or modify
## -v vol	 specify volume of ILN (e.g., 38)
##
## Rebecca Sutton Koeser, February 2003

$usage = "iln_utility.pl [mode] -f filename -v volume [-o output file]
where [mode] is one of:
  -entity-name	fix names of image entities to match image files
  -entity-list	generate entity list according to entities in files
  -entity-check verify figure entities
  -imgsize	calculate & insert image sizes (for ILN image viewer)
  -divsize	calculate & insert div lengths in paragraphs

options:
  -f		file to process
  -v		ILN volume (i.e., 38, 39, etc.)
  -o		output file (defaults to filename.new)

Note: volume *must* be specified for all modes except divsize.
";


$image_dir = "/chaucer/data/iln/images";
## default infile (for now)
$iln_file = "/chaucer/data/iln/xml/data/iln.xml";
## default volume # (for now)
#$vol = 38;


$debug = 1;

# mode variables
$entity_name = 0;
$entity_list = 0;
$entity_check = 0;
$imgsize = 0;
$divsize = 0;
$file_next = 0;
$vol_next = 0;
$outfile_next = 0;

# variables for entity-check mode
$checked = 0;
$missing = 0;
$zerosize = 0;
$pagematch = 0;
@unused = ();
@used = ();


## determine what mode we are in, get any command-line options
foreach $arg (@ARGV) {
  if ($arg =~ "-entity-name") {
    $entity_name = 1;
  } elsif ($arg =~ "-entity-list") {
    $entity_list = 1;
  } elsif ($arg =~ "-entity-check") {
    $entity_check = 1;
  } elsif ($arg =~ "-imgsize") {
    $imgsize = 1;
  } elsif ($arg =~ "-divsize" ) {
    $divsize = 1;
  } elsif ($arg =~ "-h" || $arg =~ "--help" ) {
    print $usage; exit();
  } elsif ($arg =~ "-f" ) {
    $file_next = 1;
  } elsif ($file_next) {
    $iln_file = $arg;	# grab file name
    $file_next = 0;
  } elsif ($arg =~ "-v") {
    $vol_next = 1;
  } elsif ($vol_next) {
    $vol = $arg;	# grab volume number
    $vol_next = 0;
  } elsif ($arg =~ "-o") {
    $outfile_next = 1;
  } elsif ($outfile_next) {
    $outfile = $arg;
    $outfile_next = 0;
  }
}

## no default mode
if (!($entity_name || $entity_list || $entity_check || $imgsize || $divsize)) {
  print "Error! Mode must be specified!\n\n";
  print "Usage:\n";
  print $usage;
  exit();
} elsif (($entity_name || $entity_list || $entity_check || $imgsize)  && (! $vol)) {
 print "Error!  Volume must be specified in this mode!\n\n";
 print "Usage:\n";
 print $usage;
 exit();
}




if ($imgsize) {
  use Image::Size;
}

# do prep work for entity-name & list modes (generate list of image files)
if ($entity_name || $entity_list || $entity_check) {
  opendir(IMAGEDIR, $image_dir) || die("Couldn't open dir $image_dir: $!");
  #@files = grep("ILNv38.*jpg", readdir(IMAGEDIR));
  ## why doesn't this grep work?!?
  @list = readdir(IMAGEDIR);
  closedir(IMAGEDIR);

  #only grab the images for current volume
  foreach $f (@list) {
    if ($f =~ "^ILNv${vol}p.*jpg") {  # don't include titlepage (special case)
      push(@files, $f);
    }
  }
  # sort images by page number & then abc
  @files = sort bypage @files;

}

# print out entity definitions for each figure entity
if ($entity_list) {
  foreach $f (@files) {
    $ent = entity($f);
    print "<!ENTITY $ent SYSTEM \"../images/$f\" NDATA jpeg>\n";
  }
} elsif ($entity_check) {	# set up a hash to check that all image files are used
  foreach $f (@files) {
    $imglist{$f} = 0;
  }
}

if ($entity_name || $entity_check || $imgsize || $divsize) {
  # open input/output files (mode = entity names, imgsize, or divsize)
  open(ILN, "$iln_file") || die("Couldn't open file $iln_file: $!");
  unless ($entity_check) {    ## no change to output
    unless ($outfile) { 	# use outfile name from command line, if specified
      $new_file = `basename $iln_file`;  # output file in current directory
      chop($new_file);  # get rid of newline
      $outfile = "$new_file.new";
    }
    open(OUT, ">$outfile") 
      || die("Couldn't open output file $outfile: $!");
  }

  while(<ILN>) {
    # grab current page # from pb or biblScope
    if (($entity_name || $entity_check) && /<pb n="(\d+)"/ ) {
      $cur_page = $1;
      #    if ($debug) { print "hit <pb>, page is $cur_page\n"; }
    } elsif (($entity_name || $entity_check) && /<biblScope type="pages">p+.\s*(\d+)-*\d*</ ) {
      $cur_page = $1;
      #    if ($debug) { print "hit <biblScope>, page is $cur_page\n"; }
    } elsif ($entity_name && /<figure entity="(\w*)"/) {
      $entity = $1;
      ## fix entity value
      ### FIXME: this may not be the best algorithm for doing this...
      $new_fig = entity($files[$i]);
      $new_page = page($files[$i]);
      if ($cur_page != $new_page) {
	print "Error! page numbers do not match (on $cur_page, entity belongs on $new_page).\n";
      }
      if ($entity == $new_fig) {
        print "page $cur_page: $entity seems to be correct...\n";
      } else {
        print "page $cur_page: replacing $entity with $new_fig\n";
      }
      s/entity=".*">/entity="$new_fig">/;
      $i++;
    } elsif ($imgsize && /<figure entity="(\w*)"/) {
      $entity = $1;
      if (/width="\d*"/ || /height="\d*"/) {   # check that dimensions don't exist
	print "Error! Image dimensions have already been added. Skipping entity $entity.\n";
      } else {
	# insert image dimensions into xml file
	($x, $y) = imgsize("$image_dir/ILN$entity.jpg");
	s/(entity.*)>/$1 width="$x" height="$y">/;
      }
    } elsif ($entity_check && /<figure entity="(\w*)"/) {
      $entity = $1;
      sanity_check($entity, $cur_page);
    } elsif ($entity_name && /<figure>/) {
      ## case where entity attribute does not exist -- insert it
      ### FIXME: this may not be the best algorithm for doing this...
      $new_fig = entity($files[$i]);
      $new_page = page($files[$i]);
      if ($cur_page != $new_page) {
	print "Error! page numbers do not match (on $cur_page, entity belongs on $new_page).\n";
      }
      print "page $cur_page: replacing $entity with $new_fig\n";
      s/<figure>/<figure entity="$new_fig">/;
      $i++;
    } elsif ($divsize && /<div2/ ) {	
      $p_count = 0;	# reset paragraph count at every div
    } elsif ($divsize && /<p>/ ) {
      $p_count++;	# count paragraphs in this div
    } elsif ($divsize && /<\/bibl>/ ) {
      $insert_extent = tell(OUT);  # get filehandle position to insert extent
      # print a line to fill later
      print OUT "<extent># paragraph</extent>    \n";  
    } elsif ($divsize && /<\/div2>/ ) {
      # output the number of paragraphs
      $cur_pos = tell(OUT);  # save position in file
      seek(OUT, $insert_extent, SEEK_SET);  # go to just before </bibl>
      print OUT "<extent>$p_count paragraph";
      if ($p_count > 1) { print OUT "s"; }
      print OUT "</extent>\n";
#      </bibl>\n";    # seeking overrides </bibl> line
      seek(OUT, $cur_pos, SEEK_SET);
    }
    unless ($entity_check) {   ## no new file in entity_check mode
      print OUT $_;
    }
  }

close(ILN);
close(OUT);


  if ($entity_check) {
    ## print out results
    print "
Results:
  Checked $checked figure entities in $iln_file.
  Missing image files:   $missing
  Zero size image files: $zerosize
  Mismatched pages:      $pagematch

";

    foreach $f (sort keys(%imglist)) {
      if ($imglist{$f}) {
	push(@used, $f);
      } else {
	push(@unused, $f);
      }
    }
     if ($#unused >= 0 ) {   ## FIXME: is this right?
       $total = $#unused + 1;
       if ($total == 1) {
	 print "$total volume $vol image was not used:\n\t@unused\n";
       } else {
	 print "$total volume $vol images were not used:\n";
	 foreach $l (@unused) {
	   print "\t$l\n";
	 }
       }
    } else {
      print "All images for volume $vol were used.\n";
    }

  }


}




#return the [first] page number where an image occurs
sub page {
  my($page);		
  $page = @_[0];
  $page =~ s/ILNv${vol}p//;
  $page =~ s/\.jpg//;
  $page =~ s/[ab-]\d*//;
  return $page;
}

# return the entity name for an image (everything between ILN and .jpg)
sub entity {
  my($entity);
  $entity = $1;
  $entity = @_[0];
  $entity =~ s/ILN//;
  $entity =~ s/\.jpg//;
  return $entity;
}

# sort the images by page #
sub bypage {
  my($pagea, $pageb);
  $pagea = page($a);
  $pageb = page($b);
  if ($pagea == $pageb) {  # special case: 2 or more figures on same page
    $a cmp $b;
  } else {
    page($a) <=> page($b);
  }
}

## run a couple of checks on the figure entity, to verify it
sub sanity_check {
 my($entity, $page) = @_;
 my($filename, $entity_page, $imgfile);
 $imgfile = "ILN$entity.jpg";
 $filename = "$image_dir/$imgfile";
 $entity_page = page($imgfile);   ## page subroutine expects full filename
 $imglist{$imgfile} = 1;	# mark this image as being used

 $checked++;
 if (! -e $filename) {
  print "Warning: $filename does not exist!\n";
  $missing++;
 } elsif ( -z $filename) {
  print "Warning: $filename has zero size!\n";
  $zerosize++;
 }
 if ($page != $entity_page) {
   print "Warning: entity page numbers do not match! ($entity [$entity_page] occurs on $page)\n";
   $pagematch++;
 }

}
