<html>
    <head>
        <title>Documents without Irish tag</title>
    </head>
    <body>
<h1 style="font-size:105%;">Checking for 'Irish' in titleproper type attribute</h1>
<!-- check for wrong type or no type at all -->

{if (exists(//titleproper[@type != 'Irish']) or exists(//titleproper[not(@type)])) then 
 (<div>
<p><b>documents without Irish label</b></p>
<ul>
{for $a in (//titleproper[@type != 'Irish'],//titleproper[not(@type)])
let $doc := util:document-name($a)
return <li>{$doc} 
{if (exists($a/@type)) then <span>  (type = {@type})</span> else <span>  (no type)</span>}
</li>}
</ul> 
</div>)
else (<p>All loaded documents contain 'Irish' label in titleproper type attribute</p>)
}

<hr/>
        <p>all distinct titleproper types</p>
        <ul>
{for $a in distinct-values(//titleproper/@type)
return <li>{$a}</li>}
</ul>
    </body>
</html>