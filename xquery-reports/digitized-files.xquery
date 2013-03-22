(: 
XQuery to get a list of all text notes about digitized files
in the text of the unittitle.  Searches for unittitles that contain the string "digitized",
and then splits out the portion in brackets, e.g. [digitized; filename 1234].

Generates a comma-separate list of:
  digitized note 
  entire unittitle that conained the digitized note
  filename
  manuscript id (from archdesc/unitid identifier attribute)
  box 
  folder
:)

declare namespace e='urn:isbn:1-931666-22-9';
declare namespace util='http://exist-db.org/xquery/util';

for $title in //e:unittitle[contains(., 'digitized')]
(: many unittitles contain multiple bracketed comments; restrict to digitized to grab correct one :)
let $digitized := concat('digitized', substring-before(substring-after($title, '[digitized'), ']'))
let $docname := util:document-name($title)
let $mss := $title/ancestor::e:ead//e:unitid/@identifier
let $box := $title/preceding-sibling::e:container[@type="box"]
let $folder := $title/preceding-sibling::e:container[@type="folder"]
(: return quoted, comma-delimited since unittitles may contain commas :)
return concat('"', normalize-space($digitized), '",',
    '"', normalize-space($title), '",',
    '"', normalize-space($docname), '",',
    '"', normalize-space($mss), '",',
    '"', normalize-space($box), '",',  
    '"', normalize-space($folder), '",'
    )
