package edu.columbia.ruleof72;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertAll;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class RuleOf72CalculatorTest {

    private static final double DELTA = 1.0e-9;

    private final RuleOf72Calculator calculator = new RuleOf72Calculator();

    @Test
    void calculatesAllFormulasAtOnePercent() {
        assertFormulaValues(0.01,
                69.660716893575,
                69.000000000000,
                69.346733668342,
                70.351758793970,
                69.658291457286,
                72.000000000000);
    }

    @Test
    void calculatesAllFormulasAtFivePointFivePercent() {
        assertFormulaValues(0.055,
                12.946157112237,
                12.545454545455,
                12.900210329516,
                13.087169899509,
                12.958167796214,
                13.090909090909);
    }

    @Test
    void calculatesAllFormulasAtSevenPointFivePercent() {
        assertFormulaValues(0.075,
                9.584358956628,
                9.200000000000,
                9.558441558442,
                9.696969696970,
                9.601385281385,
                9.600000000000);
    }

    @Test
    void calculatesAllFormulasAtEightPointThreePercent() {
        assertFormulaValues(0.083,
                8.693139255992,
                8.313253012048,
                8.673190414239,
                8.798888826040,
                8.712156921897,
                8.674698795181);
    }

    @Test
    void calculatesAllFormulasAtTwentyPercent() {
        assertFormulaValues(0.20,
                3.801784016924,
                3.450000000000,
                3.833333333333,
                3.888888888889,
                3.850555555556,
                3.600000000000);
    }

    @Test
    void rejectsNonPositiveRates() {
        assertThrows(IllegalArgumentException.class, () -> calculator.calculate(0.0));
    }

    private void assertFormulaValues(
            double rate,
            double exact,
            double approx1,
            double approx2,
            double approx3,
            double approx4,
            double rule72
    ) {
        RuleOf72Calculator.FormulaValues values = calculator.calculate(rate);

        assertAll(
                () -> assertEquals(exact, values.exact(), DELTA),
                () -> assertEquals(approx1, values.approx1(), DELTA),
                () -> assertEquals(approx2, values.approx2(), DELTA),
                () -> assertEquals(approx3, values.approx3(), DELTA),
                () -> assertEquals(approx4, values.approx4(), DELTA),
                () -> assertEquals(rule72, values.rule72(), DELTA)
        );
    }
}
