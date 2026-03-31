package edu.columbia.ruleof72;

public final class RuleOf72Calculator {

    public FormulaValues calculate(double r) {
        if (r <= 0.0) {
            throw new IllegalArgumentException("Interest rate r must be positive.");
        }

        double denominator = r - (r * r) / 2.0;
        if (denominator == 0.0) {
            throw new IllegalArgumentException("Taylor approximation denominator must be non-zero.");
        }

        double exact = Math.log(2.0) / Math.log(1.0 + r);
        double approx1 = 0.69 / r;
        double approx2 = 0.69 / denominator;
        double approx3 = 0.70 / denominator;
        double approx4 = 0.6931 / denominator;
        double rule72 = 72.0 / (100.0 * r);

        return new FormulaValues(exact, approx1, approx2, approx3, approx4, rule72);
    }

    public record FormulaValues(
            double exact,
            double approx1,
            double approx2,
            double approx3,
            double approx4,
            double rule72
    ) {
    }
}
