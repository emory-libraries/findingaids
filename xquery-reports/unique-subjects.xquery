(:

Generate a list of unique subjects from controlled access terms.

:)

declare namespace e='urn:isbn:1-931666-22-9';
distinct-values(
  for $s in //e:controlaccess/e:controlaccess/e:subject
  let $val := normalize-space($s)
  order by $val
  return $val
)
