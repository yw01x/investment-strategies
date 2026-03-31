# Rule of 72 Chart

This Maven project opens an interactive Swing window for comparing six doubling-time formulas:

- Exact
- Approx 1
- Approx 2
- Approx 3
- Approx 4
- Rule of 72

The chart keeps all six curves visible, lets you drag `r` from `1.0%` to `20.0%`, and highlights the current point for each formula. It also saves a PNG file named `rule_of_72_comparison.png`.

## Run

```bash
cd assignments/rule-of-72-chart
mvn compile exec:java
```

## Test

```bash
cd assignments/rule-of-72-chart
mvn test
```

## GitHub Pages

A static browser version is available at `../../docs/investment-strategies/rule-of-72/`.

To preview it locally:

```bash
cd ../..
python3 -m http.server 8000 --directory docs
```

Then open `http://localhost:8000`.

To publish it on GitHub Pages:

1. Push this repository to GitHub.
2. Open `Settings -> Pages`.
3. Set `Source` to `Deploy from a branch`.
4. Choose your main branch and the `/docs` folder.
5. Save. GitHub will publish `docs/index.html` as a static site.

## Output

- Interactive chart window
- `rule_of_72_comparison.png`
