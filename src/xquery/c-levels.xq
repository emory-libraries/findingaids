<html>
<head>
<title>c-level test</title>
</head>
<body>
<p><b>documents which contain c01, c02, c03, or c04 nodes with no level attribute</b></p>
<ul>{for $d in distinct-values(for $c in (//c01,//c02,//c03,//c04)[not(@level)]
let $doc := util:document-name($c)
return $doc)
return <li>{$d}</li>}
</ul>
<hr/>
<p><b>more details</b>: node name, id
<br/>[box #] [folder #] unittitle
<br/><i>(note: displaying first 1,000 of {count((//c01,//c02,//c03,//c04)[not(@level)])} total)</i>
</p>
<ul>
{for $c in (//c01,//c02,//c03,//c04)[not(@level)][position() >1 and position() < 1000]
return <li>{local-name($c)} id={string($c/@id)}
<br/>
{for $b in $c/did/container[@type='box'] return <span>Box: {$b} &#x00a0;</span>}
{for $f in $c/did/container[@type='folder'] return <span>Folder: {$f}&#x00a0;</span>}
{$c/did/unittitle}
</li>}
</ul>
</body>
</html>