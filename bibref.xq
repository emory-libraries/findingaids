<html>
    <head>
        <title>Documents with bibref</title>
    </head>
    <body>
<h1 style="font-size:105%;">Documents which include the bibref element</h1>

{if (exists(//bibref)) then 
 (<div>
<ul>
{for $a in (//bibref)
let $doc := util:document-name($a)
return <li>{$doc} </li>}
</ul> 
</div>)
else (<p>no loaded documents match</p>)
}

<hr/>
    </body>
</html>