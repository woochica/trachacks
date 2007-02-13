import java.applet.*;
import java.awt.*;
import java.awt.geom.*;
import java.text.*;
import java.util.*;

import org.jfree.chart.*;
import org.jfree.data.time.*;
import org.jfree.chart.axis.*;
import org.jfree.chart.plot.*;
import org.jfree.ui.*;

public class ProjectCharts extends Applet {

  public JFreeChart chart;
  private TimeTableXYDataset dataset;
  private XYPlot plot;
  private DateAxis xAxis;
  
  public void init()
  {
    dataset = new TimeTableXYDataset();
    chart = ChartFactory.createTimeSeriesChart(
      "testing", "time", "work", dataset, true, true, false);
    ChartPanel panel = new ChartPanel(chart, getWidth(), getHeight(),
      200, 150, 600, 800, true, true, true, true, true, true);
    add(panel);
    
    plot = chart.getXYPlot();
    xAxis = (DateAxis)plot.getDomainAxis();
  }
  
  static Date date(long t)
  {
    return new Date(t*1000);
  }

  static Day day(long t)
  {
    return new Day(date(t));
  }
  
  public void markTimePeriod(long min, long max, String label)
  {
    IntervalMarker marker = new IntervalMarker(min*1000, max*1000);
    marker.setLabel(label);
    marker.setLabelFont(new Font("SansSerif", Font.ITALIC, 16));
    marker.setLabelAnchor(RectangleAnchor.BOTTOM_LEFT);
    marker.setLabelTextAnchor(TextAnchor.BASELINE_LEFT);
    marker.setPaint(new Color(222, 222, 255, 128));
    plot.addDomainMarker(marker);
  }

  public void addTracTimePoint(int t, double y, String seriesName)
  {
    dataset.add(day(t), y, seriesName);
  }
}
