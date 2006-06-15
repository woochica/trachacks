<?cs include "burndown_header.cs" ?>
<?cs include "macros.cs" ?>

<script type="text/javascript">
    function drawGraph() {
        var layout = new PlotKit.Layout("bar", {});
        layout.addDataset("sqrt", [[0, 0], [1, 1], [2, 1.414], [3, 1.73], [4, 2]]);
        layout.evaluate();
        var canvas = MochiKit.DOM.getElement("graph");
        var plotter = new PlotKit.SweetCanvasRenderer(canvas, layout, {});
        plotter.render();
    }
    MochiKit.DOM.addLoadEvent(drawGraph);
</script>

<div id="content" class="burndown">
 <h1>Kip Dynamite</h1>
 <img src="<?cs var:chrome.href ?>/hw/images/kip.jpg">
</div>

<?cs include "footer.cs" ?>
