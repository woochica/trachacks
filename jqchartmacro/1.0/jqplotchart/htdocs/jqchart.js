/* vim: set ts=16 et sw=2 cindent fo=qroca: */

// Shows the tooltip.
var bindTooltip = function (additionalInfo) {
  var tooltipContentEditor = function (str, seriesIndex, pointIndex, plot) {
    var point = plot.data[seriesIndex][pointIndex];
    var info = additionalInfo[seriesIndex][pointIndex];
    return '<div style="background: rgb(208, 208, 208);">'
      + '<div>' + info[0] + '</div>'
      + '<div>' + point[0] + '</div>'
      + '<div>' + point[1] + '</div>'
      + '</div>';
  }
  return tooltipContentEditor;
}

// Goes to the ticket when the user clicks in a data point.
var bindClickHandler = function (additionalInfo) {
  var dataClickHandler = function (ev, seriesIndex, pointIndex, data) {
    if (additionalInfo[seriesIndex][pointIndex][1]) {
      window.location = additionalInfo[seriesIndex][pointIndex][1];
    }
  }
  return dataClickHandler;
}

/** Renders the chart.
 *
 * type is one of the supported charts: Pie, Bar, Donut, Line, etc.
 */
var renderChart = function (containerId, type, data, additionalInfo, useDate,
    baseOptions) {

  var meterGaugeOptions = {
    seriesDefaults: {
      renderer: jQuery.jqplot['MeterGaugeRenderer'],
      rendererOptions: {
        labelPosition: 'bottom',
        labelHeightAdjust: -5,
        intervalColors: ['#66cc66', '#E7E658', '#cc6666'],
        ringWidth: '2',
        ringColor: '#888',
        tickColor: '#888',
        background: '#fffdf6'
      }
    }
  };

  var otherOptions = {
    seriesDefaults: {
      renderer: jQuery.jqplot[type + 'Renderer'],
      rendererOptions: {
        sliceMargin: 3,
        // Put data labels on the pie slices.
        // By default, labels show the percentage of the slice.
        showDataLabels: true
      }
    }, cursor: {
      show: false,
      tooltipLocation: 'sw'
    }, highlighter: {
      show: true,
      tooltipContentEditor: bindTooltip(additionalInfo),
      sizeAdjust: 7.5,
      useAxesFormatters: false
    }, legend: {
      show: true,
      location: 'e',
      placement: 'outsideGrid'
    }
  };

  var options = {};

  // Options to use for non-date axis.
  var categoryAxisOptions = {
    axes: {
      xaxis: {
        renderer: jQuery.jqplot.CategoryAxisRenderer
      }
    }
  };

  // Options to use for a date axis.
  var dateAxisOptions = {
    axes: {
      xaxis: {
        renderer: jQuery.jqplot.DateAxisRenderer,
        tickOptions: {
          formatString: '%b %#d, %y'
        }
      }
    }
  };

  var seriesData = [];
  if (type == 'MeterGauge') {
    seriesData[0] = [];
    seriesData[0][0] = data [0][0][1];
    jQuery.extend(true, options, meterGaugeOptions);
  } else {
    seriesData = data;
    jQuery.extend(true, options, otherOptions);
    if (useDate == true) {
      jQuery.extend(true, options, dateAxisOptions);
    } else {
      jQuery.extend(true, options, categoryAxisOptions);
    }
  }

  jQuery.extend(true, options, baseOptions);

  var plot = jQuery.jqplot(containerId, seriesData, options);
  jQuery('#' + containerId).bind('jqplotDataClick',
      bindClickHandler(additionalInfo));
  if (type == 'MeterGauge' && baseOptions.gaugeClickLocation) {
    jQuery('#' + containerId + ' .jqplot-event-canvas').click(function () {
      window.location = baseOptions.baseUrl + baseOptions.gaugeClickLocation;
    });
  }
}

