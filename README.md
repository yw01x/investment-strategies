# Investment Strategies

Public course repository for Investment Strategies assignments and browser-based demos.

## Structure

- `docs/`: GitHub Pages site for instructor review
- `assignments/rule-of-72-chart/`: Java/Maven source for the Rule of 72 assignment

## Local Preview

Preview the static site:

```bash
python3 -m http.server 8000 --directory docs
```

Then open `http://localhost:8000`.

Run the Java assignment locally:

```bash
cd assignments/rule-of-72-chart
mvn test
mvn compile exec:java
```
