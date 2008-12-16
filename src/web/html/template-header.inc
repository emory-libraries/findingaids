<?
include_once("common_functions.php");

global $baseURL;

?>
<body id="findingAids">
	
	<!-- begin container -->
	<div id="container">
	
<!-- begin header --><!-- #BeginLibraryItem "/Library/header.lbi" -->
        <div id="header">
            <div id="headerPics">
                <a href="<?= $baseURL ?>/index.html" title="Emory MARBL"><img src="<?= $baseURL ?>/img/marbl-logo.jpg" id="marblLogo" alt="MARBL - Manuscript, Archives &amp; Rare Book Library" /></a>
                <div id="utilityLinks">
                    <a href="<?= $baseURL ?>/support-marbl.html" title="SUPPORT MARBL">SUPPORT MARBL</a>
                    <a href="<?= $baseURL ?>/contact-marbl.html" title="CONTACT US">CONTACT US</a>
                </div>



<form action="http://search.emory.edu/search" method="get" id="searchForm">
                    <p>
                        <input type="text" size="20" class="searchInput" value="Search The Site" id="q" name="q" onfocus="if(this.value == 'Search The Site') { this.value = ''; }" onblur="if(this.value == '') { this.value = 'Search The Site'; }"/>

                        <input type="image" src="<?= $baseURL ?>/img/search-btn.gif" name="Submit" alt="Submit" value="Submit" id="searchbutton" class="searchBtn" />
                    		<input type="hidden" name="site" value="marbl_library" /> 
      						<input type="hidden" name="ud" value="1" /> 
    						<input type="hidden" name="oe" value="UTF-8" /> 
      						<input type="hidden" name="ie" value="UTF-8" />   
      						<input type="hidden" name="proxystylesheet" value="marbl_frontend" />  
      						<input type="hidden" name="output" value="xml_no_dtd" />
      						<input type="hidden" name="client" value="marbl_frontend" />  
                    
                    </p>
                    <p>
                        <a href="<?= $baseURL ?>/search-marbl-collections.html" title="Search MARBL Collections">Search MARBL Collections</a>

                    </p>
                </form>

            </div>
        </div>
<!-- #EndLibraryItem --><!-- end header -->
	
<!-- begin global navigation --><!-- #BeginLibraryItem "/Library/globalNav.lbi" -->
        <div id="globalNav">
            <ul id="menu">
                <li id="skip"><a href="#skip-nav" title="Skip Navigation">Skip Navigation</a></li>
                <li id="homeNav"><a href="<?= $baseURL ?>/index.html" title="Home"><span>Home</span></a></li>
                <li id="aboutNav"><a href="<?= $baseURL ?>/vision.html" title="About MARBL"><span>About MARBL</span></a></li>
              <li id="collectionNav"><a href="<?= $baseURL ?>/marbl-collections.html" title="Collection Overview"><span>Collection Overview</span></a></li>
                <li id="researchNav"><a href="<?= $baseURL ?>/search-marbl-collections.html" title="Conduct Research"><span>Conduct Research</span></a></li>
                <li id="eventsNav"><a href="<?= $baseURL ?>/events-and-exhibitions.html" title="Events &amp; Exhibitions"><span>Events &amp; Exhibitions</span></a></li>
                <li id="visitNav"><a href="<?= $baseURL ?>/directions-and-hours.html" title="Visit MARBL"><span>Visit MARBL</span></a></li>
          </ul>
        </div>
        <a name="skip-nav" title="Skip Navigation"></a>
<!-- #EndLibraryItem --><!-- end global navigation -->     

		<!-- begin interiorContainer -->
        <div id="interiorContainer">
		
			<!-- begin leftColumn -->
			<div id="leftCol">

				<!-- begin interiorNav -->
				<ul id="interiorNav">
					<li class="selected"><a href="<?= $baseURL ?>/search-marbl-collections.html" title="Search MARBL Collections">Search MARBL Collections</a></li>
				</ul>
				<!-- end interiorNav -->
                
                <form action="search.php" method="get" class="searchFindingAidsForm">
					<h4>Search All Finding Aids</h4>
                    <p>
<!--						<input type="radio" name="searchFindingAidsOption" id="thisFindingAid" value="thisFindingAid" class="radio" checked="checked" /><label for="thisFindingAid">This Finding Aid</label><br />
						<input type="radio" name="searchFindingAidsOption" id="allFindingAids" value="allFindingAids" class="radio" /><label for="allFindingAids">All Finding Aids</label> -->
					<input name="keyword"
						type="text" size="20"
						class="searchInput" />
						<input type="image"
						src="<?= $baseURL ?>/img/go-btn.gif" class="searchBtn" />
                    </p> 
                    <p><a href="browse.php" title="Browse all Finding Aids" class="carrotLink">Browse All Finding Aids</a></p>
                </form>
                
                <div id="relatedLinks">
					<h2>Related Links</h2>
					<ul>
<!--			<li><a href="" title="Help Using Finding Aids">Help Using Finding Aids</a></li> -->
                        <li><a href="<?= $baseURL ?>/introduction-to-collections.html" title="Introduction to Collections">Introduction to Collections</a></li>
                        <li><a href="<?= $baseURL ?>/using-marbl.html" title="Using MARBL">Using MARBL</a></li>
                        <li><a href="<?= $baseURL ?>/for-visiting-researchers.html" title="Visiting MARBL">Visiting MARBL</a></li>
                        <li><a href="http://www.library.emory.edu" title="Emory Libraries Catalog" onclick="target='_blank'">Emory Libraries Catalog</a></li>
					</ul>
				</div>
				
			</div>
			<!-- end left column -->
			
			<!-- begin rightColWide-->
			<div id="rightColWide">



															       
