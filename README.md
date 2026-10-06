# Pay Equity Regression: Simulated Company Example

**Question:** does a company pay women, or employees of a given race or ethnicity, less than comparable colleagues, and how large is the gap once job-related factors are accounted for?

**Method:** multiple linear regression (often called multivariate regression in HR and compensation work) on pay in dollars, built up in three steps by adding one block of controls at a time.

**Important:** every employee in this project is **simulated**. No real company or person is involved. I generated 2,000 fictional employees and built pay gaps of known size into the pay formula, so the analysis can be checked against the truth. Real engagements use a client's confidential HR data.

| Notebook | Script | Data |
|---|---|---|
| [Pay Equity Simulated Example.ipynb](Pay%20Equity%20Simulated%20Example.ipynb) (also as [HTML](Pay%20Equity%20Simulated%20Example.html)) | [simple_pay_equity_regression.py](simple_pay_equity_regression.py) | [simulated_company_pay_data.csv](simulated_company_pay_data.csv) (simulated) |

## Approach in four steps

1. **Simulate the company** (2,000 employees with known built-in pay gaps)
2. **Check the data** (missing values, duplicates, ranges, group sizes)
3. **Explore** (raw pay gaps and who reaches the best-paid job levels)
4. **Regression** (three models, adding controls one block at a time)

---

## Step 1. The data

The table has one row per employee. Each employee's characteristics were drawn at random, then pay was calculated from a formula.

| Column | Meaning | How it was made |
|---|---|---|
| `Gender` | Female or Male | 47% female |
| `Race` | White, Black, Hispanic, Asian | 58% / 13% / 17% / 12% |
| `Age` | Years, 22 to 64 | Centered on 40 |
| `Experience` | Years of work experience | Based on age (older means more) |
| `Tenure` | Years at the company | Never more than experience |
| `Education` | 1 = high school, 2 = bachelor's, 3 = master's, 4 = PhD | 20% / 50% / 25% / 5% |
| `Location` | High-, mid- or low-cost area | 30% / 40% / 30% |
| `Dept` | Engineering, Sales, Operations, Corporate | 30% / 25% / 30% / 15% |
| `JobLevel` | 1 to 5 | Rises with experience, tenure and education, but women, Black and Hispanic employees are somewhat less likely to reach the higher levels |
| `Pay` | Annual pay in dollars | Calculated from the formula below |
| `Female` | 1 if female, else 0 | Created from `Gender` |
| `Age40Plus` | 1 if age 40 or over, else 0 | Created from `Age` |

**The pay formula (the "truth" the regression should recover):**

> Pay = $42,000 + $8,500 per job level above 1 + $700 per year of experience + $900 per year of tenure + $2,500 per education step + location premium (high $8,000, mid $3,500, low $0) + department premium (Engineering $6,000, Sales $2,000, Corporate $1,500, Operations $0) **− $3,500 if female − $3,000 if Black − $2,000 if Hispanic** + random noise of about $5,000

So the built-in pay gaps, with everything else equal, are: women -$3,500, Black employees -$3,000, Hispanic employees -$2,000, Asian employees $0, age 40+ $0.

## Step 2. Data checks and cleaning

| Check | Result |
|---|---|
| Rows and columns | 2,000 rows, 12 columns |
| Missing values | 0 |
| Duplicate rows | 0 |
| Value ranges | Age 22 to 64, experience 0 to 45 years, tenure 0 to 20 years, education 1 to 4, job level 1 to 5, pay $34,574 to $146,479 |
| Tenure never exceeds experience | Yes |
| `Age40Plus` agrees with `Age` | Yes |
| Group sizes | 944 women and 1,056 men; 1,181 White, 322 Hispanic, 262 Black, 235 Asian |

**Cleaning needed:** none. **Rows removed:** none. This data is clean by construction because it was simulated. Real HR data normally needs cleaning here: missing values, inconsistent job titles, part-time and partial-year pay, and duplicate records.

**Columns created:** `Female` (0/1 from `Gender`, because regression needs numbers) and `Age40Plus` (0/1 flag from `Age`). Regression also converts `Race`, `Location`, `Dept` and `JobLevel` into 0/1 columns automatically, one per category except a reference category (White, high-cost, Corporate and level 1 are not named in the output; each coefficient reads as a difference from the reference).

## Step 3. Exploration

| | Average pay |
|---|---|
| Women | $76,110 |
| Men | $83,502 |
| White | $81,252 |
| Asian | $84,790 |
| Hispanic | $76,904 |
| Black | $73,963 |

The raw gap between women and men is $7,392 (8.9% of men's average pay). A raw gap compares people in different jobs and at different career stages, so it doesn't yet say whether like is being compared with like. The next chart shows part of why: women and Black and Hispanic employees are less likely to reach the best-paid job levels (4 and 5).

![Who reaches senior levels](images/02_who_reaches_senior_levels.png)

## Step 4. Regression

### The variables

| Role | Variables |
|---|---|
| **Dependent variable** (what we explain) | `Pay`, annual pay in dollars |
| **Protected characteristics** (what we test) | `Female`; `Race` (Black, Hispanic, Asian, compared with White); `Age40Plus` |
| **Job-related controls** | `Experience`, `Tenure`, `Education`, `Location`, `Dept` |
| **Contested control** | `JobLevel` |

### The three equations, in the order they were run

Each model keeps everything from the one before and adds one block of controls.

**Model 1: protected characteristics only (the raw gaps)**

```
Pay = b0 + b1·Female + b2·Black + b3·Hispanic + b4·Asian + error
```

**Model 2: adds job-related factors**

```
Pay = b0 + b1·Female + b2·Black + b3·Hispanic + b4·Asian + b5·Age40Plus
         + b6·Experience + b7·Tenure + b8·Education + location + department + error
```

**Model 3: adds job level**

```
Pay = b0 + b1·Female + b2·Black + b3·Hispanic + b4·Asian + b5·Age40Plus
         + b6·Experience + b7·Tenure + b8·Education + location + department + job level + error
```

### Why this order

1. **Model 1 first** gives the baseline: how large are the gaps before comparing anyone to anyone?
2. **Model 2** adds factors that clearly affect pay for legitimate reasons (experience, tenure, education, location, department). If a gap remains, it isn't explained by these.
3. **Model 3 last** adds job level, because it is the contested control. Level strongly drives pay, but if some groups are less likely to be promoted, controlling for level can make pay look fairer than the system is. Comparing Models 2 and 3 shows how much of each gap runs through job level.

### How to read a coefficient

Each `b` is a slope: how many dollars pay changes when that variable goes up by one, holding the other variables equal. For a 0/1 flag such as `Female`, going up by one means going from 0 to 1, so the slope is the pay gap between the two groups. The `Female` coefficient compares women with comparable men; each race coefficient compares that group with comparable White employees. Standard errors are robust (HC3).

### Results

![Regression results](images/01_regression_results.png)

| Group | Model 1 (raw) | Model 2 (+ job factors) | Model 3 (+ job level) | Built-in truth |
|---|---|---|---|---|
| Female | -$7,314 | -$7,111 | **-$3,511** | -$3,500 |
| Black | -$7,220 | -$6,618 | **-$3,061** | -$3,000 |
| Hispanic | -$4,299 | -$4,130 | **-$1,497** | -$2,000 |
| Asian | +$3,419 | +$453 (not significant) | +$296 (not significant) | $0 |
| Age 40+ | not in model | +$623 (not significant) | +$129 (not significant) | $0 |
| R-squared | 0.06 | 0.80 | 0.94 | |

For Model 3 the 95% ranges are: Female -$3,973 to -$3,049; Black -$3,743 to -$2,378; Hispanic -$2,110 to -$884; Asian -$426 to +$1,019; Age 40+ -$602 to +$861. All three built-in gaps fall inside their ranges, and the two groups with no built-in gap include $0.

**How to read the numbers**
- **Coefficient:** the pay difference in dollars versus comparable colleagues in the reference group. Negative means paid less.
- **95% range:** where the true gap very likely lies. If it contains $0, the gap can't be told apart from chance.
- **p-value:** below 0.05 means statistically significant.
- **R-squared:** the share of pay differences the model explains (0.06 = 6%, 0.94 = 94%).

## Findings

1. **Women, Black employees and Hispanic employees show statistically significant pay gaps** after comparing people with the same experience, tenure, education, location, department and job level: about $3,500, $3,100 and $1,500 respectively.
2. **Asian employees and employees aged 40+ show no significant gap.**
3. **The regression recovers the built-in gaps.** That shows the method works when the data is well specified.
4. **Raw gaps are larger than adjusted gaps** (women: about $7,300 raw versus about $3,500 at the same level). The difference runs through job level: women and Black and Hispanic employees reach the best-paid levels less often.
5. **Model 2 versus Model 3** separates two things: the pay gap between people at the same level, and the gap that comes from some groups reaching senior levels less often.

## Context: real pay equity analyses

- **Salesforce** runs a pay assessment each year (seven since 2015) covering nearly 70,000 employees across gender and race/ethnicity. In its latest reported assessment, 8.5% of employees needed pay adjustments, at a cost of $5.6 million, with more than $22 million spent cumulatively since 2015. [Salesforce, 2022 equal pay update](https://www.salesforce.com/news/stories/2022-equal-pay-update-the-salesforce-approach-to-pay-fairness/)
- **Glassdoor**, using more than 505,000 salaries, found men earn 24.1% more in base pay on average. Comparing workers with the same job title, employer and location, the gap falls to 5.4%. [Glassdoor, "Demystifying the Gender Pay Gap"](https://www.glassdoor.com/blog/gender-pay-gap/)
- **Blau and Kahn (2017, NBER)** studied U.S. panel data from 1980 to 2010 and found that by 2010 conventional human capital variables explained little of the gender wage gap, while occupation and industry segregation remained important. [NBER working paper 21913](https://www.nber.org/papers/w21913)

## Limitations

- The data is simulated, so the results show the method works, not that any real company has these gaps.
- The model assumes each group's gap is the same at every job level. A real audit would test interactions and run separate models by job family.
- Gender is binary and race has four groups, which is simpler than real data. Real audits also consider more categories and more controls.
- Regression shows association, not proof of discrimination.

## Run it yourself

```bash
pip install pandas numpy matplotlib statsmodels
python simple_pay_equity_regression.py     # or open the notebook / run cell by cell in Spyder
```

The script generates the simulated data (fixed random seed, so results repeat), saves `simulated_company_pay_data.csv`, and writes two charts to `images/`.
