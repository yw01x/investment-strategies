package edu.columbia.ruleof72;

import java.util.Arrays;

public final class MadHedgeCalculator {

    private MadHedgeCalculator() {
    }

    public static double median(double[] values) {
        if (values == null || values.length == 0) {
            throw new IllegalArgumentException("Input array must be non-empty.");
        }

        double[] copy = Arrays.copyOf(values, values.length);
        Arrays.sort(copy);

        int n = copy.length;
        if (n % 2 == 1) {
            return copy[n / 2];
        } else {
            return (copy[n / 2 - 1] + copy[n / 2]) / 2.0;
        }
    }

    public static double mad(double[] returns) {
        if (returns == null || returns.length == 0) {
            throw new IllegalArgumentException("Return series must be non-empty.");
        }

        double med = median(returns);
        double[] absDeviations = new double[returns.length];

        for (int i = 0; i < returns.length; i++) {
            absDeviations[i] = Math.abs(returns[i] - med);
        }

        return median(absDeviations);
    }

    public static double[] hedgedReturns(double[] optionReturns, double[] spyReturns, double h) {
        if (optionReturns == null || spyReturns == null || optionReturns.length != spyReturns.length || optionReturns.length == 0) {
            throw new IllegalArgumentException("Return arrays must be non-empty and have the same length.");
        }

        double[] hedged = new double[optionReturns.length];
        for (int i = 0; i < optionReturns.length; i++) {
            hedged[i] = optionReturns[i] + h * spyReturns[i];
        }
        return hedged;
    }

    public static double madForHedge(double[] optionReturns, double[] spyReturns, double h) {
        return mad(hedgedReturns(optionReturns, spyReturns, h));
    }

    public static double findBestMadHedge(
            double[] optionReturns,
            double[] spyReturns,
            double hMin,
            double hMax,
            double step
    ) {
        if (step <= 0.0) {
            throw new IllegalArgumentException("Step size must be positive.");
        }

        double bestH = hMin;
        double bestMad = Double.POSITIVE_INFINITY;

        for (double h = hMin; h <= hMax; h += step) {
            double currentMad = madForHedge(optionReturns, spyReturns, h);
            if (currentMad < bestMad) {
                bestMad = currentMad;
                bestH = h;
            }
        }

        return bestH;
    }
}
