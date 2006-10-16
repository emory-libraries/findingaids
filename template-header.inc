<?
include_once("common_functions.php");

$baseURL  = "http://marbl.library.emory.edu";

?>
<body background="<?= $baseURL ?>/images/common/global_bg.jpg">
<table border="0" cellpadding="0" cellspacing="0" width="100%" align="center">
	<!-- ~~~~~~~~~~~~~~~~~~~~~~~  HEADER - VERY TOP ~~~~~~~~~~~~~~~~~~~~~~~ -->
	<tr>
		<td colspan="3">
			<table border="0" cellpadding="0" cellspacing="0" width="100%" background="<?= $baseURL ?>/images/subpage/subtop_bg.gif">
				<tr>
					<td align="left"><img src="<?= $baseURL ?>/images/subpage/subtop_1.gif" width="619" height="4" alt=""/></td>
					<td align="right"><img src="<?= $baseURL ?>/images/subpage/subtop_2.gif" width="87" height="4" alt=""/></td>
				</tr>
			</table>
		</td>
	</tr>

	<tr>
		<td valign="top" width="5" background="<?= $baseURL ?>/images/common/shadow_left_bg.gif"><img src="<?= $baseURL ?>/images/subpage/sub_shadow_left.gif" width="5" height="225" alt=""></td>
		<td valign="top" width="100%" bgcolor="#FFFFFF">

			<!-- ~~~~~~~~~~~~~~~~~~~~~~~  LOGO & STRETCH PICTURE  ~~~~~~~~~~~~~~~~~~~~~~~ -->
			<table border="0" cellpadding="0" cellspacing="0" width="100%" class="subLogoBg">
				<tr>
					<td align="left"><a href="http://www.emory.edu/libraries.cfm"><img src="<?= $baseURL ?>/images/subpage/sublogo.gif" alt="" width="252" height="118" border="0"></a></td>
					<td align="right"><img src="<?= $baseURL ?>/images/subpage/top_photo_MARBL.jpg" width="459" height="118" alt="" usemap="#_stretch" border="0"></td>
				</tr>
			</table>

			<!-- ~~~~~~~~~~~~~~~~~~~~~~~  NAVIGATION & SEARCH  ~~~~~~~~~~~~~~~~~~~~~~~ -->
			<table border="0" cellpadding="0" cellspacing="0" width="100%">
				<tr>
					<td bgcolor="#FFFFFF"><img src="<?= $baseURL ?>/images/common/spacer.gif" width="1" height="1" alt=""></td>
				</tr>
				<tr>
					<td bgcolor="#465074" align="left">
 
						<table border="0" cellpadding="0" cellspacing="0">
							<tr>
								<td><a href="http://web.library.emory.edu/" onmouseover="swapImg('navmain','<?= $baseURL ?>/images/nav/main_off.gif');" onmouseout="swapImg('navmain','<?= $baseURL ?>/images/nav/main_on.gif');"><img src="<?= $baseURL ?>/images/nav/main_on.gif" width="75" height="25" alt="" border="0" name="navmain"></a></td>
								<td><a href="http://chemistry.library.emory.edu/" onmouseover="swapImg('navchemistry','<?= $baseURL ?>/images/nav/chemistry_on.gif');" onmouseout="swapImg('navchemistry','<?= $baseURL ?>/images/nav/chemistry_off.gif');"><img src="<?= $baseURL ?>/images/nav/chemistry_off.gif" width="86" height="25" alt="" border="0" name="navchemistry"></a></td>
								<td><a href="http://musicmedia.library.emory.edu/" onmouseover="swapImg('navmusicmedia','<?= $baseURL ?>/images/nav/musicmedia_on.gif');" onmouseout="swapImg('navmusicmedia','<?= $baseURL ?>/images/nav/musicmedia_off.gif');"><img src="<?= $baseURL ?>/images/nav/musicmedia_off.gif" width="106" height="25" alt="" border="0" name="navmusicmedia"></a></td>
								<td><a href="http://marbl.library.emory.edu/" onmouseover="swapImg('navmarbl','<?= $baseURL ?>/images/nav/marbl_on.gif');" onmouseout="swapImg('navmarbl','<?= $baseURL ?>/images/nav/marbl_off.gif');"><img src="<?= $baseURL ?>/images/nav/marbl_off.gif" width="63" height="25" alt="" border="0" name="navmarbl"></a></td>
								<td><a href="http://www.emory.edu/OXFORD/Library/" onmouseover="swapImg('navoxford','<?= $baseURL ?>/images/nav/oxford_on.gif');" onmouseout="swapImg('navoxford','<?= $baseURL ?>/images/nav/oxford_off.gif');"><img src="<?= $baseURL ?>/images/nav/oxford_off.gif" width="72" height="25" alt="" border="0" name="navoxford"></a></td>
								<td><a href="http://business.library.emory.edu/" onmouseover="swapImg('navbusiness','<?= $baseURL ?>/images/nav/business_on.gif');" onmouseout="swapImg('navbusiness','<?= $baseURL ?>/images/nav/business_off.gif');"><img src="<?= $baseURL ?>/images/nav/business_off.gif" width="81" height="25" alt="" border="0" name="navbusiness"></a></td>
								<td><a href="http://www.healthlibrary.emory.edu/" onmouseover="swapImg('navhealth','<?= $baseURL ?>/images/nav/health_on.gif');" onmouseout="swapImg('navhealth','<?= $baseURL ?>/images/nav/health_off.gif');"><img src="<?= $baseURL ?>/images/nav/health_off.gif" width="74" height="25" alt="" border="0" name="navhealth"></a></td>
								<td><a href="http://www.law.emory.edu/library/" onmouseover="swapImg('navlaw','<?= $baseURL ?>/images/nav/law_on.gif');" onmouseout="swapImg('navlaw','<?= $baseURL ?>/images/nav/law_off.gif');"><img src="<?= $baseURL ?>/images/nav/law_off.gif" width="56" height="25" alt="" border="0" name="navlaw"></a></td>
								<td><a href="http://www.pitts.emory.edu/" onmouseover="swapImg('navtheology','<?= $baseURL ?>/images/nav/theology_on.gif');" onmouseout="swapImg('navtheology','<?= $baseURL ?>/images/nav/theology_off.gif');"><img src="<?= $baseURL ?>/images/nav/theology_off.gif" width="83" height="25" alt="" border="0" name="navtheology"></a></td>					
							</tr>
						</table>
						
					</td>
				</tr>
				<tr>
					<td bgcolor="#FFFFFF"><img src="<?= $baseURL ?>/images/common/spacer.gif" width="1" height="1" alt=""></td>
				</tr>
				<tr>
					<td background="<?= $baseURL ?>/images/common/tbl_search_bg.gif" align="left">
  <form method="get" action="http://web.library.emory.edu/search/reURL.php">

						<table border="0" cellpadding="0" cellspacing="0" width="696" height="33">
                                                        <tr>
                                                                <td background="<?= $baseURL ?>/images/common/search_field_bg.gif" width="328" class="searchText">
                                                                        &nbsp;&nbsp;&nbsp;&nbsp;
									<input type="text" name="search" maxlength="50" class="searchField" value="quick search" onfocus="FormSearch(this, 1)" onblur="FormSearch(this, 0)"> &nbsp;&nbsp;<input type="radio" checked name="host" value="euclid">EUCLID Catalog 
									&nbsp;&nbsp;
									<input type="radio" name="host" value="gl">Library Info
                                                                </td>
                                                                <td width="89" background="<?= $baseURL ?>/images/common/search_btn_bg.gif">
									<input type="Image" src="<?= $baseURL ?>/images/common/btn_global_search.gif" width="45" height="10" alt="Search" name="Go" value="Go">
								</td>
                                                                <td width="279">
								</td>
                                                        </tr>
						</table>
									                                                        </form>
									
					</td>
				</tr>
				<tr>
					<td bgcolor="#FFFFFF"><img src="<?= $baseURL ?>/images/common/spacer.gif" width="1" height="8" alt=""></td>
				</tr>				
			</table>


