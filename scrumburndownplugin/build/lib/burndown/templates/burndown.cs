<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div id="content" class="burndown">
 <h1>Burndown Chart</h1>
</div>

<!-- graph code begins here-->
<script src="/cgi-bin/trac.cgi/chrome/hw/js/line.js" type="text/javascript"></script>
<script src="/cgi-bin/trac.cgi/chrome/hw/js/wz_jsgraphics.js" type="text/javascript"></script>

<div id="myCanvas" style="overflow: auto; position:relative;height:480px;width:640px;"></div>

<script>
var g = new line_graph();
g.add('1', 145);
g.add('2', 0);
g.add('3', 175);
g.add('4', 130);
g.add('5', 150);
g.add('6', 175);
g.add('7', 205);
g.add('8', 125);
g.add('9', 125);
g.add('10', 135);
g.add('11', 125);
g.add('12', 145);
g.add('13', 0);
g.add('14', 175);
g.add('15', 130);
g.add('16', 150);
g.add('17', 175);
g.add('18', 205);
g.add('19', 125);
g.add('20', 125);
g.add('21', 135);
g.add('22', 125);
g.add('23', 145);
g.add('24', 0);
g.add('25', 175);
g.add('26', 130);
g.add('27', 150);
g.add('28', 175);
g.add('29', 205);
g.add('30', 125);
g.add('31', 125);
g.add('32', 135);
g.add('33', 125);
g.add('34', 145);
g.add('35', 0);
g.add('36', 175);
g.add('37', 130);
g.add('38', 150);
g.add('39', 175);
g.add('40', 205);
g.add('41', 125);
g.add('42', 125);
g.add('43', 135);
g.add('44', 125);

//If called without a height parameter, defaults to 250
//g.render("myCanvas", "test graph");

g.render("myCanvas", "test graph", 400);

</script>
<!-- graph code ends here-->

<?cs include "footer.cs" ?>
