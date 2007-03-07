<html>
<head>
<title>Check eadid against document name</title>
</head>
<body>
<p><b>documents where eadid does not match document name</b></p>
<ul>
{for $id in //eadid
let $doc := util:document-name($id)
where $id != $doc
return 
<li> <b>eadid:</b> &#x00a0; {string($id)}<br/>
<b>document name:</b>  &#x00a0; {$doc}</li>}
</ul>
</body>
</html>