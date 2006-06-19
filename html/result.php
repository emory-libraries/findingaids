<?
require_once("common_functions.php");

?>


<div style="float:left; width: 300px; height:100%;">
	<iframe name="toc" src="<?= $toc ?>" style="width:99%; height:1000px;"></iframe>
</div>

<div style="margin-left: 310px; height:100%">
	<div style="height:50px;">
		<div class="pageHeader">
			<? displayBreadCrumbs($crumbs); ?>
		</div>
		<p />
		<? include("html/MARBL-bar.inc"); ?>
	</div>
	<br />
	<iframe name="content" src="<?= $content ?>" style="width:99%; height:940px;"></iframe>

</div>






<!--
<div style="float:left;">
<iframe name="toc" id="toc" src="" height="1000px"></iframe>
</div>
<div style="float:left;">
<iframe name="content" id="content" src="" height="1000px"></iframe>
</div>

<script language="JavaScript">
  window.onResize = setSize();
  
  function setSize()
  {
	document.getElementById('toc').width = self.innerWidth * 0.27;
	document.getElementById('content').width = self.innerWidth * 0.7;
  }
</script>
-->