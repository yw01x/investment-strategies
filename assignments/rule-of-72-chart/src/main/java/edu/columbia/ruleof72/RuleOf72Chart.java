package edu.columbia.ruleof72;

import org.knowm.xchart.BitmapEncoder;
import org.knowm.xchart.XChartPanel;
import org.knowm.xchart.XYChart;
import org.knowm.xchart.XYChartBuilder;
import org.knowm.xchart.XYSeries;
import org.knowm.xchart.style.lines.SeriesLines;
import org.knowm.xchart.style.markers.Marker;
import org.knowm.xchart.style.markers.SeriesMarkers;

import javax.swing.BorderFactory;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JSlider;
import javax.swing.JTextArea;
import javax.swing.SwingUtilities;
import javax.swing.WindowConstants;
import javax.swing.event.ChangeEvent;
import javax.swing.event.ChangeListener;
import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Font;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Hashtable;
import java.util.List;
import java.util.Locale;
import java.util.function.ToDoubleFunction;

public class RuleOf72Chart {

    static final int MIN_SLIDER_VALUE = 10;
    static final int MAX_SLIDER_VALUE = 200;
    static final int DEFAULT_SLIDER_VALUE = 83;

    private static final String OUTPUT_BASENAME = "rule_of_72_comparison";
    private static final FormulaDefinition[] FORMULAS = {
            new FormulaDefinition("Exact", new Color(31, 119, 180), SeriesMarkers.CIRCLE,
                    RuleOf72Calculator.FormulaValues::exact),
            new FormulaDefinition("Approx 1", new Color(255, 127, 14), SeriesMarkers.DIAMOND,
                    RuleOf72Calculator.FormulaValues::approx1),
            new FormulaDefinition("Approx 2", new Color(44, 160, 44), SeriesMarkers.SQUARE,
                    RuleOf72Calculator.FormulaValues::approx2),
            new FormulaDefinition("Approx 3", new Color(214, 39, 40), SeriesMarkers.TRIANGLE_UP,
                    RuleOf72Calculator.FormulaValues::approx3),
            new FormulaDefinition("Approx 4", new Color(148, 103, 189), SeriesMarkers.OVAL,
                    RuleOf72Calculator.FormulaValues::approx4),
            new FormulaDefinition("Rule of 72", new Color(140, 86, 75), SeriesMarkers.CROSS,
                    RuleOf72Calculator.FormulaValues::rule72)
    };

    private final RuleOf72Calculator calculator = new RuleOf72Calculator();
    private final JTextArea valuesArea = createValuesArea();

    private XYChart chart;
    private XChartPanel<XYChart> chartPanel;
    private JFrame frame;

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> new RuleOf72Chart().show());
    }

    static double sliderValueToRate(int sliderValue) {
        if (sliderValue < MIN_SLIDER_VALUE || sliderValue > MAX_SLIDER_VALUE) {
            throw new IllegalArgumentException("Slider value out of range: " + sliderValue);
        }
        return sliderValue / 1000.0;
    }

    private void show() {
        double initialRate = sliderValueToRate(DEFAULT_SLIDER_VALUE);
        RuleOf72Calculator.FormulaValues initialValues = calculator.calculate(initialRate);

        chart = buildChart(initialRate, initialValues);
        chartPanel = new XChartPanel<>(chart);
        chartPanel.setBorder(BorderFactory.createEmptyBorder(8, 8, 8, 8));

        frame = new JFrame("Interactive Rule of 72 Comparator");
        frame.setDefaultCloseOperation(WindowConstants.EXIT_ON_CLOSE);
        frame.setLayout(new BorderLayout());
        frame.add(chartPanel, BorderLayout.CENTER);
        frame.add(createValuesPanel(initialRate, initialValues), BorderLayout.EAST);
        frame.add(createSliderPanel(), BorderLayout.SOUTH);
        frame.pack();
        frame.setLocationByPlatform(true);
        frame.setVisible(true);

        saveChart();
    }

    private XYChart buildChart(double initialRate, RuleOf72Calculator.FormulaValues initialValues) {
        List<Double> rateValues = new ArrayList<>();
        List<List<Double>> allSeriesValues = new ArrayList<>();
        for (int i = 0; i < FORMULAS.length; i++) {
            allSeriesValues.add(new ArrayList<>());
        }

        for (int sliderValue = MIN_SLIDER_VALUE; sliderValue <= MAX_SLIDER_VALUE; sliderValue++) {
            double rate = sliderValueToRate(sliderValue);
            RuleOf72Calculator.FormulaValues values = calculator.calculate(rate);
            rateValues.add(rate);

            for (int i = 0; i < FORMULAS.length; i++) {
                allSeriesValues.get(i).add(FORMULAS[i].value(values));
            }
        }

        XYChart xyChart = new XYChartBuilder()
                .width(1050)
                .height(720)
                .title("Interactive Comparison of Doubling-Time Approximations")
                .xAxisTitle("r (decimal interest rate)")
                .yAxisTitle("n (doubling time)")
                .build();

        xyChart.getStyler().setLegendVisible(true);
        xyChart.getStyler().setMarkerSize(10);
        xyChart.getStyler().setXAxisMin(sliderValueToRate(MIN_SLIDER_VALUE));
        xyChart.getStyler().setXAxisMax(sliderValueToRate(MAX_SLIDER_VALUE));
        xyChart.getStyler().setYAxisMin(0.0);

        for (int i = 0; i < FORMULAS.length; i++) {
            FormulaDefinition formula = FORMULAS[i];
            XYSeries lineSeries = xyChart.addSeries(formula.label(), rateValues, allSeriesValues.get(i));
            lineSeries.setLineColor(formula.color());
            lineSeries.setLineWidth(2.0f);
            lineSeries.setMarker(SeriesMarkers.NONE);
        }

        for (FormulaDefinition formula : FORMULAS) {
            XYSeries pointSeries = xyChart.addSeries(currentPointName(formula.label()),
                    new double[]{initialRate},
                    new double[]{formula.value(initialValues)});
            pointSeries.setShowInLegend(false);
            pointSeries.setLineStyle(SeriesLines.NONE);
            pointSeries.setLineColor(formula.color());
            pointSeries.setMarkerColor(formula.color());
            pointSeries.setMarker(formula.marker());
        }

        return xyChart;
    }

    private JPanel createValuesPanel(double initialRate, RuleOf72Calculator.FormulaValues initialValues) {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBorder(BorderFactory.createTitledBorder("Current Values"));
        panel.add(valuesArea, BorderLayout.CENTER);
        valuesArea.setText(buildValuesText(initialRate, initialValues));
        return panel;
    }

    private JPanel createSliderPanel() {
        JSlider slider = new JSlider(JSlider.HORIZONTAL, MIN_SLIDER_VALUE, MAX_SLIDER_VALUE, DEFAULT_SLIDER_VALUE);
        slider.setMajorTickSpacing(10);
        slider.setMinorTickSpacing(1);
        slider.setPaintTicks(true);
        slider.setPaintLabels(true);
        slider.setLabelTable(buildSliderLabels());

        JLabel hintLabel = new JLabel("Drag r from 1.0% to 20.0% in 0.1% steps.");
        JPanel panel = new JPanel(new BorderLayout(0, 8));
        panel.setBorder(BorderFactory.createEmptyBorder(8, 12, 12, 12));
        panel.add(hintLabel, BorderLayout.NORTH);
        panel.add(slider, BorderLayout.CENTER);

        ChangeListener listener = new ChangeListener() {
            @Override
            public void stateChanged(ChangeEvent event) {
                double rate = sliderValueToRate(slider.getValue());
                RuleOf72Calculator.FormulaValues values = calculator.calculate(rate);
                refreshCurrentState(rate, values);

                if (!slider.getValueIsAdjusting()) {
                    saveChart();
                }
            }
        };
        slider.addChangeListener(listener);

        return panel;
    }

    private Hashtable<Integer, JLabel> buildSliderLabels() {
        Hashtable<Integer, JLabel> labels = new Hashtable<>();
        labels.put(10, new JLabel("1%"));
        labels.put(50, new JLabel("5%"));
        labels.put(100, new JLabel("10%"));
        labels.put(150, new JLabel("15%"));
        labels.put(200, new JLabel("20%"));
        return labels;
    }

    private void refreshCurrentState(double rate, RuleOf72Calculator.FormulaValues values) {
        for (FormulaDefinition formula : FORMULAS) {
            chart.updateXYSeries(
                    currentPointName(formula.label()),
                    new double[]{rate},
                    new double[]{formula.value(values)},
                    null
            );
        }

        valuesArea.setText(buildValuesText(rate, values));
        chartPanel.revalidate();
        chartPanel.repaint();
    }

    private String buildValuesText(double rate, RuleOf72Calculator.FormulaValues values) {
        StringBuilder builder = new StringBuilder();
        builder.append(String.format(Locale.US, "r = %.3f (%.1f%%)%n%n", rate, rate * 100.0));
        for (FormulaDefinition formula : FORMULAS) {
            builder.append(String.format(Locale.US, "%-11s %.4f%n",
                    formula.label() + ":",
                    formula.value(values)));
        }
        return builder.toString();
    }

    private JTextArea createValuesArea() {
        JTextArea textArea = new JTextArea(10, 24);
        textArea.setEditable(false);
        textArea.setFocusable(false);
        textArea.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 14));
        textArea.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));
        return textArea;
    }

    private void saveChart() {
        try {
            BitmapEncoder.saveBitmap(chart, OUTPUT_BASENAME, BitmapEncoder.BitmapFormat.PNG);
        } catch (IOException exception) {
            if (frame != null) {
                JOptionPane.showMessageDialog(
                        frame,
                        "Unable to save PNG: " + exception.getMessage(),
                        "Save Error",
                        JOptionPane.ERROR_MESSAGE
                );
            }
        }
    }

    private static String currentPointName(String label) {
        return label + " Current";
    }

    private record FormulaDefinition(
            String label,
            Color color,
            Marker marker,
            ToDoubleFunction<RuleOf72Calculator.FormulaValues> extractor
    ) {
        double value(RuleOf72Calculator.FormulaValues values) {
            return extractor.applyAsDouble(values);
        }
    }
}
