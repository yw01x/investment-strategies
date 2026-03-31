package edu.columbia.ruleof72;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class RuleOf72ChartTest {

    private static final double DELTA = 1.0e-12;

    @Test
    void mapsSliderValueTenToOnePercent() {
        assertEquals(0.010, RuleOf72Chart.sliderValueToRate(10), DELTA);
    }

    @Test
    void mapsSliderValueFiftyFiveToFivePointFivePercent() {
        assertEquals(0.055, RuleOf72Chart.sliderValueToRate(55), DELTA);
    }

    @Test
    void mapsSliderValueEightyThreeToEightPointThreePercent() {
        assertEquals(0.083, RuleOf72Chart.sliderValueToRate(83), DELTA);
    }

    @Test
    void mapsSliderValueTwoHundredToTwentyPercent() {
        assertEquals(0.200, RuleOf72Chart.sliderValueToRate(200), DELTA);
    }
}
