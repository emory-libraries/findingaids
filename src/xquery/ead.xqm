module namespace eadxq = "http://www.library.emory.edu/xquery/eadxq";

declare namespace text = "http://exist-db.org/xquery/text";

import module namespace phrase="http://www.library.emory.edu/xquery/phrase" at
    "xmldb:exist:///db/xquery-modules/phrase.xqm";


(:
: xquery functions for EAD finding aid documents
:)

(:~
: return all elements necessary to build a table of contents for the finding aid
: 
: @param ead root document element
: @return toc element with selected ead sections and headers
:)
declare function eadxq:toc($ead as element(ead), 
  			   $keyword as xs:string?, 
  			   $phrase as xs:string?) as node() {
  let $archdesc := $ead/archdesc
  return <toc>
	   <ead>{$ead/@id}
		<name>
			{string($archdesc/did/origination/persname)}
			{string($archdesc/did/origination/corpname)}
			{string($archdesc/did/origination/famname)}
		</name>
		<eadheader>
			<filedesc>
              <titlestmt>{$ead/eadheader/filedesc/titlestmt/titleproper}</titlestmt>
            </filedesc>
		</eadheader>
		<archdesc>
		  <did>
	            {$archdesc/did/unittitle}
                    {eadxq:hits($archdesc/did, $keyword, $phrase)}
		  </did>
	     <collectiondescription>
               {eadxq:hits(($archdesc//bioghist, $archdesc//scopecontent), $keyword, $phrase)}
             </collectiondescription>
             <controlaccess>
               {eadxq:hits($archdesc//controlaccess, $keyword, $phrase)}
             </controlaccess>

		  <index>
	    	    {$archdesc/index/@id}
                    {$archdesc/index/head}
                    {eadxq:hits($archdesc/index, $keyword, $phrase)}
	          </index>

			<dsc>
				{$archdesc/dsc/head}
                          {eadxq:hits($archdesc/dsc, $keyword, $phrase)}
	
			{for $c in $archdesc/dsc/c01[@level='series']
			 return <c01> 
				 {$c/@id}
		            	 {$c/@level}
	                        {eadxq:hits($c, $keyword, $phrase)}
				 {if (exists($c/c02)) then <c02/> else ()}
				<did>
					{$c/did/unitid}
					{$c/did/unittitle}
   					{$c/did/physdesc}
				</did>
  			  </c01>}
	    	</dsc>
		  </archdesc>
	   </ead>
  </toc>
};

(:~
: shortcut version of toc function without keyword or phrase
:)
declare function eadxq:toc($ead as element(ead)) as node() {
 eadxq:toc($ead, "", "")
};

(:~
: shortcut version of toc function without phrase
:)
declare function eadxq:toc($ead as element(ead), $keyword as xs:string) as node() {
 eadxq:toc($ead, $keyword, "")
};

(:~
: convenience function to call the appropriate content function depending on element type
:)
declare function eadxq:content($element as element(),
  			       $keyword as xs:string,
			       $phrase as xs:string) as node() {
(: filter on keyword to get full-text higlighting :)
 let $el := (if ($keyword != "" and exists($element[. |= $keyword])) then
     $element[. |= $keyword]
    else $element)
 return 
  if (name($el) = 'ead') then
  eadxq:content-ead($el, $keyword, $phrase)
 else 
  eadxq:content-c($el, $phrase)
};

declare function eadxq:content($element as element()) as node() {
  eadxq:content($element, "", "")
};


(:~
: xml needed for content page when element is ead (not entire ead)
:)
declare function eadxq:content-ead($ead as element(ead), 
	$keyword as xs:string,
	$phrase as xs:string) as node() {
	 <ead>
   		  {$ead/@id}
		  {phrase:tag-matches($ead/eadheader, $phrase)}
		  {phrase:tag-matches($ead/frontmatter, $phrase)}
		 <archdesc>
	 	{phrase:tag-matches($ead/archdesc/*[not(self::dsc)], $phrase)}
		{for $dsc in $ead/archdesc/dsc return eadxq:dsc($dsc, $keyword, $phrase)}
	 </archdesc>
	</ead> 
};

(: FIXME: would header or frontmatter ever be displayed / need highlighting ? :)


(:~
: c-series node
: returns ancestor c01 id to allow highlighting context in TOC
:)
declare function eadxq:content-c($el as element(), $phrase as xs:string) as node() {
  <ead>
    {phrase:tag-matches($el, $phrase)}
    {for $parent in  $el/ancestor::c01
    return <parent id="{$parent/@id}"/> }
  </ead>
};

declare function eadxq:dsc($dsc as element(dsc), 
	$keyword as xs:string,
	$phrase as xs:string) as node()* {
   for $d in $dsc
   return <dsc> 
			{$d/@*}
		   	{$d/head}
		   {phrase:tag-matches($d/c01[@level != 'series'], $phrase)}
		   {for $c01 in $d/c01[c02 or @level='series']
		    return <c01>
		      {$c01/@*}
		      {$c01/did}
        	      {eadxq:hits($c01, $keyword, $phrase)}
		      {for $c02 in $c01/c02[@level='subseries']
			return <c02>
			 	 {$c02/@*}
				 {$c02/did}
			     {for $c03 in $c02/c03[c04]
				return <c03>
				 {$c03/@*}
				 {$c03/did}
		       </c03> }
	      </c02> }
	    </c01> }
    </dsc>
};

declare function eadxq:dsc($dsc as element(dsc)) as node()* {
    eadxq:dsc($dsc, "", "")
};




declare function eadxq:hits($el as element()*, 
			    $keyword as xs:string, 
			    $phrase as xs:string) as node() {
    <hits>{
     sum(eadxq:keyword-count($el, $keyword) + phrase:count($el, $phrase)) 
     }
   </hits>
};


declare function eadxq:keyword-count($el as element()*, 
				     $keyword as xs:string) as xs:int {
    if ($keyword = '') then	0
    else 
       sum(for $matchel in ($el)[. |= $keyword]
       return text:match-count($matchel))	  
};
