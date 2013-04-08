(:

XQuery to search for EAD documents that do NOT have "unrestricted access" in
the text of the accessrestrict.

Generates a comma-separated list with the following fields:
  origination name (persname, famname, or corpname)
  unit title
  access restrict (all paragraphs separated by a space)
:)

declare namespace e='urn:isbn:1-931666-22-9';
for $ad in /e:ead/e:archdesc[not(contains(e:accessrestrict/e:p, 'Unrestricted access'))]
let $name := $ad/e:did/e:origination/e:persname|$ad/e:did/e:origination/e:famname|$ad/e:did/e:origination/e:corpname
let $title := $ad/e:did/e:unittitle
let $access := string-join($ad/e:accessrestrict/e:p, ' ')
(: return quoted, comma-delimited since many names and titles contain commas :)
return concat('"', normalize-space($name), '",',
    '"', normalize-space($title), '",',
    '"', normalize-space($access), '"')