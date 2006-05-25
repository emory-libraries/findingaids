#!/bin/tcsh

## add a doctype header (really could be any file) to a text file
## usage: add_doctype.sh doctype file

set doctype_file = $argv[1];
set file = $argv[2];
set exscript = "/tmp/add_doctype";


echo "0r $doctype_file" > $exscript;
echo "write" >> $exscript;
echo "quit" >> $exscript;

ex $file < $exscript;

rm $exscript;
