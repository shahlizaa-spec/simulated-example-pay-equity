# %% [markdown]
# # A Simple Pay Equity Regression (SIMULATED example company)
#
# **Important: every employee below is simulated.** There is no real company or person here.
# I created the data on purpose, with pay gaps built in at known sizes, so we can check that
# the regression finds them. Real engagements use a client's confidential HR data.
#
# **The scenario.** "A company asks: do we pay women, or employees of a given race or
# ethnicity, less than comparable colleagues?"
#
# **The method.** Multiple linear regression (often called multivariate regression in HR work):
#
#     Pay = b0 + b1*Female + b2*Black + b3*Hispanic + b4*Asian + b5*Age40Plus
#               + b6*Experience + b7*Tenure + b8*Education + location + department + job level + error
#
# Each coefficient (b) is a *slope*: how many dollars pay changes when that variable goes up by
# one unit, holding everything else in the model equal. For a 0/1 flag such as Female, "one unit"
# means going from 0 to 1, so the slope is the pay gap between the two groups.

# %%
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf

os.makedirs("images", exist_ok=True)
rng = np.random.default_rng(42)
N = 2000

# %% [markdown]
# ## Step 1. Simulate the company
#
# The pay formula below is the "truth" that the regression will try to recover. The built-in
# pay gaps, holding everything else equal, are: **women -$3,500, Black employees -$3,000,
# Hispanic employees -$2,000, Asian employees $0, age 40+ $0.**
#
# I also make women and minority employees somewhat less likely to reach the higher job levels.
# This is realistic and is why the raw gap ends up bigger than the built-in one.

# %%
female   = rng.random(N) < 0.47
race     = rng.choice(["White", "Black", "Hispanic", "Asian"], size=N, p=[0.58, 0.13, 0.17, 0.12])
age      = np.clip(rng.normal(40, 10, N), 22, 64).round()
experience = np.clip(age - 22 - rng.normal(1, 2, N), 0, None).round()          # years of work before/at hire
tenure   = np.round(rng.uniform(0.1, 1.0, N) * np.minimum(experience, 20), 1)   # years at this company
education = rng.choice([1, 2, 3, 4], size=N, p=[0.20, 0.50, 0.25, 0.05])        # 1 HS, 2 Bachelor's, 3 Master's, 4 PhD
location = rng.choice(["High-cost", "Mid-cost", "Low-cost"], size=N, p=[0.30, 0.40, 0.30])
dept     = rng.choice(["Engineering", "Sales", "Operations", "Corporate"], size=N, p=[0.30, 0.25, 0.30, 0.15])

# Job level (1 to 5): driven by experience, tenure and education, but women and minority
# employees are somewhat less likely to reach higher levels.
latent = (0.08 * experience + 0.06 * tenure + 0.35 * (education - 1) + rng.normal(0, 1, N)
          - 0.55 * female - 0.45 * (race == "Black") - 0.35 * (race == "Hispanic"))
level = pd.cut(latent, bins=np.quantile(latent, [0, 0.30, 0.60, 0.80, 0.93, 1.0]),
               labels=[1, 2, 3, 4, 5], include_lowest=True).astype(int)

loc_prem  = pd.Series(location).map({"High-cost": 8000, "Mid-cost": 3500, "Low-cost": 0}).values
dept_prem = pd.Series(dept).map({"Engineering": 6000, "Sales": 2000, "Operations": 0, "Corporate": 1500}).values

pay = (42000 + 8500 * (level - 1) + 700 * experience + 900 * tenure + 2500 * (education - 1)
       + loc_prem + dept_prem
       - 3500 * female - 3000 * (race == "Black") - 2000 * (race == "Hispanic")   # built-in pay gaps
       + rng.normal(0, 5000, N))                                                  # everything we cannot see

df = pd.DataFrame({
    "Gender": np.where(female, "Female", "Male"), "Race": race, "Age": age.astype(int),
    "Age40Plus": (age >= 40).astype(int), "Experience": experience, "Tenure": tenure,
    "Education": education, "Location": location, "Dept": dept, "JobLevel": level,
    "Pay": pay.round(0)})
df["Female"] = (df["Gender"] == "Female").astype(int)
df.to_csv("simulated_company_pay_data.csv", index=False)
df.head()

# %% [markdown]
# ## Step 2. Check the data
#
# Before any modelling, confirm the table is complete and sensible: no missing values, no
# duplicate rows, values inside realistic ranges, and every group large enough to analyse.
# (Real HR data usually needs cleaning at this point. This data is simulated, so it is clean by
# construction, but the checks are the same ones a real analysis would run.)

# %%
print("Rows, columns:", df.shape)
print("Missing values:", int(df.isna().sum().sum()))
print("Duplicate rows:", int(df.duplicated().sum()))
print("\nValue ranges:")
print(df[["Age", "Experience", "Tenure", "Education", "JobLevel", "Pay"]].agg(["min", "max"]).T.to_string())
print("\nTenure never exceeds experience:", bool((df["Tenure"] <= df["Experience"]).all()))
print("Age40Plus agrees with Age:", bool(((df["Age"] >= 40).astype(int) == df["Age40Plus"]).all()))
print("\nEmployees per group:")
print(df["Gender"].value_counts().to_string())
print(df["Race"].value_counts().to_string())
print("\nColumns in the table:", list(df.columns))

# %% [markdown]
# Nothing needs to be removed or fixed: no missing values, no duplicates, every value is in range
# and every group has well over 100 people. The columns I created on top of the raw simulated
# fields are `Female` (0/1 version of Gender, because regression needs numbers) and `Age40Plus`
# (0/1 flag for age 40 or over, our "other protected characteristic"). Regression also turns
# Race, Location, Dept and JobLevel into 0/1 columns automatically, one per category except a
# reference category, so no extra columns are stored in the table for those.

# %% [markdown]
# ## Step 3. Look before modelling: the raw gaps and who sits where

# %%
print(f"Employees: {len(df)}   Women: {df['Female'].mean():.0%}")
print("\nAverage pay by gender:")
print(df.groupby("Gender")["Pay"].mean().round(0).to_string())
print("\nAverage pay by race/ethnicity:")
print(df.groupby("Race")["Pay"].mean().round(0).to_string())

print("\nShare of each group at job levels 4 and 5 (the best-paid levels):")
senior = df.assign(Senior=df["JobLevel"] >= 4)
print((senior.groupby("Gender")["Senior"].mean() * 100).round(1).to_string())
print((senior.groupby("Race")["Senior"].mean() * 100).round(1).to_string())

# %% [markdown]
# ## Step 4. Three regression models
#
# Same idea as before: start simple and add one block of controls at a time.
#
# * **Model 1** compares by gender and race only (the raw gaps).
# * **Model 2** adds legitimate job-related factors: experience, tenure, education, location,
#   department, plus age 40+ (a protected characteristic we also want to test).
# * **Model 3** adds job level.
#
# `White` is the reference race and `Male` is the reference gender, so the Female coefficient reads
# "compared with comparable men" and each race coefficient reads "compared with comparable White
# employees of the same gender".

# %%
race_term = "C(Race, Treatment('White'))"
formulas = {
    "Model 1: gender and race only":
        f"Pay ~ Female + {race_term}",
    "Model 2: + experience, tenure, education, location, department, age 40+":
        f"Pay ~ Female + {race_term} + Age40Plus + Experience + Tenure + Education + C(Location) + C(Dept)",
    "Model 3: + job level":
        f"Pay ~ Female + {race_term} + Age40Plus + Experience + Tenure + Education + C(Location) + C(Dept) + C(JobLevel)",
}
fits = {name: smf.ols(f, data=df).fit(cov_type="HC3") for name, f in formulas.items()}

# %%
names = {"Female": "Female", f"{race_term}[T.Black]": "Black", f"{race_term}[T.Hispanic]": "Hispanic",
         f"{race_term}[T.Asian]": "Asian", "Age40Plus": "Age 40+"}
rows = []
for model, m in fits.items():
    ci = m.conf_int()
    for term, label in names.items():
        if term in m.params:
            rows.append({"model": model[:7], "group": label, "gap_usd": m.params[term],
                         "ci_low": ci.loc[term, 0], "ci_high": ci.loc[term, 1], "p_value": m.pvalues[term]})
res = pd.DataFrame(rows)
res["significant"] = res["p_value"] < 0.05
print(res.round(3).to_string(index=False))
print("\nR-squared (share of pay differences explained):")
for name, m in fits.items():
    print(f"  {name[:7]}: {m.rsquared:.2f}")

truth = {"Female": -3500, "Black": -3000, "Hispanic": -2000, "Asian": 0, "Age 40+": 0}
print("\nBuilt-in (true) gaps:", truth)

# %% [markdown]
# **How to read the table**
# * `gap_usd` is the coefficient: the pay difference in dollars versus comparable colleagues in the
#   reference group (men for gender, White employees for race). Negative means paid less.
# * `ci_low` / `ci_high` is the 95% range. If it contains 0, we can't tell the gap from chance.
# * `p_value` below 0.05 means statistically significant.
# * R-squared is the share of pay differences the model explains.

# %%
fig, ax = plt.subplots(figsize=(10, 6))
groups = ["Female", "Black", "Hispanic", "Asian", "Age 40+"]
colors = {"Model 1": "#9AA5B1", "Model 2": "#6A9FD0", "Model 3": "#1F4E8C"}
offset = {"Model 1": 0.22, "Model 2": 0.0, "Model 3": -0.22}
seen = set()
for gi, g in enumerate(groups[::-1]):
    for mk in colors:
        sub = res[(res["group"] == g) & (res["model"] == mk)]
        if sub.empty:              # Age 40+ is not in Model 1
            continue
        r = sub.iloc[0]
        y = gi + offset[mk]
        ax.plot([r.ci_low, r.ci_high], [y, y], color=colors[mk], lw=2.4)
        ax.plot(r.gap_usd, y, "o", color=colors[mk], markersize=8,
                label=mk if mk not in seen else None, zorder=3)
        seen.add(mk)
    ax.plot(truth[g], gi - 0.42, marker="^", color="black", markersize=7,
            label="Built-in true gap" if "truth" not in seen else None)
    seen.add("truth")
ax.axvline(0, color="black", ls="--", lw=1)
ax.set_yticks(range(len(groups))); ax.set_yticklabels(groups[::-1])
ax.set_xlabel("Pay difference vs comparable colleagues in the reference group (dollars), with 95% range")
ax.set_title("What the regression finds (simulated company)")
ax.legend(loc="lower left", fontsize=9)
plt.tight_layout(); plt.savefig("images/01_regression_results.png", dpi=150); plt.show()

# %%
fig, ax = plt.subplots(figsize=(9, 4.8))
groups_sen = {"Men": df["Gender"] == "Male", "Women": df["Gender"] == "Female",
              "White": df["Race"] == "White", "Black": df["Race"] == "Black",
              "Hispanic": df["Race"] == "Hispanic", "Asian": df["Race"] == "Asian"}
share = {k: (df.loc[v, "JobLevel"] >= 4).mean() * 100 for k, v in groups_sen.items()}
bars = ax.bar(list(share), list(share.values()), color=["#3A6EA5", "#C2456B", "#9AA5B1", "#9AA5B1", "#9AA5B1", "#9AA5B1"])
for b, v in zip(bars, share.values()):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.4, f"{v:.0f}%", ha="center")
ax.set_ylabel("% of group at job level 4 or 5")
ax.set_title("Who reaches the best-paid levels (simulated company)")
plt.tight_layout(); plt.savefig("images/02_who_reaches_senior_levels.png", dpi=150); plt.show()
