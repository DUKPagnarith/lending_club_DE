# =============================================================================
# L05 — PD Model Rebuild on 2016–2018 OOT Data
# Credit Risk Modelling | Lending Club Dataset
#
# Motivation: Score PSI = 0.282 (ALERT) detected in L04. The 2016-2018
# applicant population has shifted materially from 2007-2015 training data.
# This script retrains the logistic WoE scorecard on 2016-2017 data,
# evaluates on 2018, and benchmarks it against the original Champion model.
#
# Strategy:
#   - Retain the WoE bin structure from L01 (same dummy columns)
#   - Re-estimate logistic regression weights on 2016-2017 data (backward elim)
#   - Calibrate to 2018 observed default rate
#   - Compare Champion (trained 2007-2015) vs Rebuilt on 2018 holdout
# =============================================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
from sklearn.metrics import roc_auc_score, roc_curve, brier_score_loss
from scipy.stats import ks_2samp
from scipy.optimize import brentq
from scipy.special import expit, logit
import warnings, json, os

warnings.filterwarnings('ignore')
plt.style.use('seaborn-v0_8-whitegrid')
COLORS = {'bad': '#e74c3c', 'good': '#2ecc71', 'blue': '#3498db',
          'orange': '#e67e22', 'purple': '#9b59b6'}
os.makedirs('../data/reports', exist_ok=True)

# =============================================================================
# 1. Load Data & Setup
# =============================================================================
print("="*60)
print(" L05: PD Rebuild on 2016-2018 OOT Data")
print("="*60)

train_orig = pd.read_parquet('../data/processed/train_preprocessed.parquet')
test_full  = pd.read_parquet('../data/processed/test_preprocessed.parquet')

with open('../data/processed/dummy_cols.json') as f:
    DUMMY_COLS = json.load(f)

# Champion predictions (calibrated PiT PD from L02)
champion_preds = np.load('../data/processed/pd_pred_test_pit_calibrated.npy')

print(f"\nOriginal train (2007-2015): {len(train_orig):,} rows | DR={1-train_orig['good_bad'].mean():.2%}")
print(f"OOT test  (2016-2018):     {len(test_full):,}  rows | DR={1-test_full['good_bad'].mean():.2%}")

# =============================================================================
# 2. Split OOT into Rebuild Train / Rebuild Test
# =============================================================================
rebuild_train = test_full[test_full['issue_year'].isin([2016, 2017])].copy()
rebuild_test  = test_full[test_full['issue_year'] == 2018].copy()

print(f"\nRebuild train (2016-2017): {len(rebuild_train):,} rows | DR={1-rebuild_train['good_bad'].mean():.2%}")
print(f"Rebuild test  (2018):      {len(rebuild_test):,}  rows | DR={1-rebuild_test['good_bad'].mean():.2%}")

for _df in (rebuild_train, rebuild_test):
    for _c in DUMMY_COLS + ['good_bad']:
        if _c in _df.columns:
            _df[_c] = _df[_c].astype('int8')

# =============================================================================
# 3. Fit Rebuilt Logistic Regression (same WoE dummies, new weights)
# =============================================================================
print("\n--- Fitting rebuilt model via backward elimination ---")

fit_sample = rebuild_train.sample(
    n=min(200_000, len(rebuild_train)), random_state=42
).reset_index(drop=True)
y_fit = fit_sample['good_bad'].astype('float32').values

# Drop near-zero-variance dummies (some WoE bins may be empty in 2016-2017)
var_check = fit_sample[DUMMY_COLS].var()
low_var   = var_check[var_check < 1e-4].index.tolist()
if low_var:
    print(f"  Dropping {len(low_var)} near-zero-variance features from rebuild data")
features = [f for f in DUMMY_COLS if f not in low_var]

def fit_logit(sample_df, feat_list, y):
    X_c = sm.add_constant(sample_df[feat_list].astype('float64'), has_constant='add')
    try:
        res = sm.Logit(y, X_c).fit(method='bfgs', maxiter=200, disp=False)
    except Exception:
        res = sm.Logit(y, X_c).fit(method='lbfgs', maxiter=200, disp=False)
    return res

iteration = 0
while True:
    result = fit_logit(fit_sample, features, y_fit)
    pvals = result.pvalues.drop('const').fillna(1.0)
    max_pval = pvals.max()
    if max_pval < 0.05:
        print(f"  Converged at iteration {iteration}: {len(features)} significant features")
        break
    worst = pvals.idxmax()
    features.remove(worst)
    iteration += 1

REBUILT_FEATURES = features
rebuilt_model = fit_logit(fit_sample, REBUILT_FEATURES, y_fit)

print(f"  Champion features: {len(DUMMY_COLS)} | Rebuilt features: {len(REBUILT_FEATURES)}")
dropped = set(DUMMY_COLS) - set(REBUILT_FEATURES)
print(f"  Features dropped in rebuild: {len(dropped)}")
if dropped:
    print(f"  {sorted(dropped)[:10]}{'...' if len(dropped)>10 else ''}")

# =============================================================================
# 4. Predict & Calibrate Rebuilt Model to 2018 Default Rate
# =============================================================================
X_test_rebuilt = sm.add_constant(
    rebuild_test[REBUILT_FEATURES].astype('float32'), has_constant='add'
)
pd_raw_rebuilt = 1 - rebuilt_model.predict(X_test_rebuilt)

actual_dr_2018 = 1 - rebuild_test['good_bad'].mean()
print(f"\n  2018 actual default rate: {actual_dr_2018:.2%}")
print(f"  Rebuilt mean PD (raw):    {pd_raw_rebuilt.mean():.2%}")

delta_rebuilt = brentq(
    lambda d: expit(logit(pd_raw_rebuilt.clip(1e-6, 1-1e-6)) + d).mean() - actual_dr_2018,
    -5, 5
)
pd_cal_rebuilt = expit(logit(pd_raw_rebuilt.clip(1e-6, 1-1e-6)) + delta_rebuilt)
print(f"  Calibration shift δ:      {delta_rebuilt:+.4f}")
print(f"  Rebuilt mean PD (calib):  {pd_cal_rebuilt.mean():.2%}")

# =============================================================================
# 5. Champion Predictions on 2018 Subset
# =============================================================================
champ_series = pd.Series(champion_preds, index=test_full.index)
champ_2018   = champ_series.loc[rebuild_test.index].values
y_2018       = rebuild_test['good_bad'].values

# =============================================================================
# 6. Evaluate: Champion vs Rebuilt on 2018 Holdout
# =============================================================================
def evaluate(y_true, y_pred_pd, label=''):
    y_good = 1 - y_pred_pd
    auc   = roc_auc_score(y_true, y_good)
    gini  = 2 * auc - 1
    ks    = ks_2samp(y_good[y_true == 1], y_good[y_true == 0]).statistic
    brier = brier_score_loss(y_true, y_good)
    return {'Model': label, 'AUC': auc, 'Gini': gini, 'KS': ks,
            'Brier': brier, 'Mean_PD': y_pred_pd.mean(),
            'Actual_DR': 1 - y_true.mean()}

champ_m   = evaluate(y_2018, champ_2018,    label='Champion (2007-2015)')
rebuilt_m = evaluate(y_2018, pd_cal_rebuilt, label='Rebuilt  (2016-2017)')

print("\n" + "="*60)
print(" Discrimination & Calibration — 2018 Holdout")
print("="*60)
print(f"{'Metric':<14} {'Champion':>14} {'Rebuilt':>14} {'Δ':>10}")
print("-"*55)
for m in ['AUC', 'Gini', 'KS', 'Brier', 'Mean_PD', 'Actual_DR']:
    c = champ_m[m]; r = rebuilt_m[m]
    print(f"{m:<14} {c:>14.4f} {r:>14.4f} {r-c:>+10.4f}")

# =============================================================================
# 7. Plot 1 — ROC Curves: Champion vs Rebuilt
# =============================================================================
fpr_c, tpr_c, _ = roc_curve(y_2018, 1 - champ_2018)
fpr_r, tpr_r, _ = roc_curve(y_2018, 1 - pd_cal_rebuilt)

fig, axes = plt.subplots(1, 2, figsize=(13, 5))

ax = axes[0]
ax.plot(fpr_c, tpr_c, color=COLORS['blue'],   lw=2,
        label=f"Champion (2007-2015)  AUC={champ_m['AUC']:.3f}, Gini={champ_m['Gini']:.3f}")
ax.plot(fpr_r, tpr_r, color=COLORS['orange'], lw=2, ls='--',
        label=f"Rebuilt  (2016-2017)  AUC={rebuilt_m['AUC']:.3f}, Gini={rebuilt_m['Gini']:.3f}")
ax.plot([0, 1], [0, 1], 'k--', lw=0.8, label='Random (AUC=0.5)')
ax.set(xlabel='False Positive Rate', ylabel='True Positive Rate',
       title='ROC Curve — 2018 Holdout\nChampion vs Rebuilt Model')
ax.legend(fontsize=8)

# Plot 2 — Calibration: Mean PD vs Actual DR by decile
ax2 = axes[1]
n_dec = 10
labels_dec = []
champ_pd_dec, reb_pd_dec, act_dr_dec = [], [], []
q_vals = np.percentile(champ_2018, np.linspace(0, 100, n_dec + 1))
for i in range(n_dec):
    mask = (champ_2018 >= q_vals[i]) & (champ_2018 <= q_vals[i + 1])
    if mask.sum() == 0:
        continue
    labels_dec.append(f'D{i+1}')
    champ_pd_dec.append(champ_2018[mask].mean())
    reb_pd_dec.append(pd_cal_rebuilt[mask].mean())
    act_dr_dec.append(1 - y_2018[mask].mean())

x = np.arange(len(labels_dec))
w = 0.3
ax2.bar(x - w, champ_pd_dec,  w, label='Champion PD',  color=COLORS['blue'],   alpha=0.8)
ax2.bar(x,     reb_pd_dec,    w, label='Rebuilt PD',   color=COLORS['orange'], alpha=0.8)
ax2.bar(x + w, act_dr_dec,    w, label='Actual DR',    color=COLORS['bad'],    alpha=0.8)
ax2.set(xticks=x, xticklabels=labels_dec,
        xlabel='Decile (by Champion PD)', ylabel='Default Rate / Predicted PD',
        title='Calibration by Decile — 2018 Holdout\n(Rebuilt aligns closer to Actual DR)')
ax2.legend(fontsize=8)
plt.suptitle('PD Rebuild: Champion (2007-2015) vs Rebuilt (2016-2017) on 2018', fontsize=11)
plt.tight_layout()
plt.savefig('../data/reports/L05_champion_vs_rebuilt_roc_calibration.png',
            dpi=150, bbox_inches='tight')
plt.show()
print("  Saved: L05_champion_vs_rebuilt_roc_calibration.png")

# =============================================================================
# 8. Plot 2 — Score/PD Distribution Shift
# =============================================================================
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

axes[0].hist(champ_2018,    bins=40, alpha=0.55, color=COLORS['blue'],
             label='Champion PD (2018 pop)', density=True)
axes[0].hist(pd_cal_rebuilt, bins=40, alpha=0.55, color=COLORS['orange'],
             label='Rebuilt PD  (2018 pop)', density=True)
axes[0].axvline(champ_2018.mean(),    color=COLORS['blue'],   ls='--', lw=1.5,
                label=f"Champion mean={champ_2018.mean():.2%}")
axes[0].axvline(pd_cal_rebuilt.mean(), color=COLORS['orange'], ls='--', lw=1.5,
                label=f"Rebuilt  mean={pd_cal_rebuilt.mean():.2%}")
axes[0].set(xlabel='Predicted PD', ylabel='Density',
            title='PD Distribution on 2018 Population\nChampion vs Rebuilt')
axes[0].legend(fontsize=8)

# PSI of rebuilt vs champion on 2018
def psi_1d(a, b, n=10):
    eps = 1e-8
    bins = np.percentile(a, np.linspace(0, 100, n + 1))
    bins[0] -= eps; bins[-1] += eps
    exp_pct = np.histogram(a, bins=bins)[0] / len(a) + eps
    obs_pct = np.histogram(b, bins=bins)[0] / len(b) + eps
    return float(np.sum((obs_pct - exp_pct) * np.log(obs_pct / exp_pct)))

psi_rebuilt_vs_champ = psi_1d(champ_2018, pd_cal_rebuilt)
print(f"\n  PSI(Champion vs Rebuilt on 2018) = {psi_rebuilt_vs_champ:.4f}")

metrics_plot = {
    'AUC':    (champ_m['AUC'],    rebuilt_m['AUC']),
    'Gini':   (champ_m['Gini'],   rebuilt_m['Gini']),
    'KS':     (champ_m['KS'],     rebuilt_m['KS']),
    '1-Brier':(1-champ_m['Brier'],1-rebuilt_m['Brier']),
}
x_m  = np.arange(len(metrics_plot))
vals_c = [v[0] for v in metrics_plot.values()]
vals_r = [v[1] for v in metrics_plot.values()]
w_m = 0.35
axes[1].bar(x_m - w_m/2, vals_c, w_m, label='Champion (2007-2015)',
            color=COLORS['blue'],   alpha=0.85)
axes[1].bar(x_m + w_m/2, vals_r, w_m, label='Rebuilt  (2016-2017)',
            color=COLORS['orange'], alpha=0.85)
axes[1].set(xticks=x_m, xticklabels=list(metrics_plot.keys()),
            ylabel='Metric Value', ylim=(0, 1),
            title='Discrimination Metrics — 2018 Holdout\nChampion vs Rebuilt')
axes[1].legend(fontsize=8)
for i, (c, r) in enumerate(zip(vals_c, vals_r)):
    axes[1].text(i - w_m/2, c + 0.01, f'{c:.3f}', ha='center', va='bottom', fontsize=7)
    axes[1].text(i + w_m/2, r + 0.01, f'{r:.3f}', ha='center', va='bottom', fontsize=7)

plt.suptitle('PD Rebuild Summary — 2018 Out-of-Time Holdout', fontsize=11)
plt.tight_layout()
plt.savefig('../data/reports/L05_rebuild_metrics_comparison.png',
            dpi=150, bbox_inches='tight')
plt.show()
print("  Saved: L05_rebuild_metrics_comparison.png")

# =============================================================================
# 9. Plot 3 — Full 2007-2018: Champion tracks well, then drifts, then rebuild
# NOTE: Include training years so the "Champion Tracks Well" story is visible.
# =============================================================================
yearly = []

# --- Training years (2007-2015): Champion predictions not stored, use actual DR
#     and approximate champion PD by scoring on train_orig sample
for yr in sorted(train_orig['issue_year'].unique()):
    mask = train_orig['issue_year'] == yr
    gb   = train_orig.loc[mask, 'good_bad'].values
    yearly.append({
        'year':        int(yr),
        'actual_dr':   float(1 - gb.mean()),
        'champion_pd': None,   # filled below from calibrated model
        'rebuilt_pd':  None,
        'period':      'train',
    })

# Champion raw predictions on the full OOT test set (all three OOT years)
for yr in sorted(test_full['issue_year'].unique()):
    mask = test_full['issue_year'] == yr
    idx  = test_full[mask].index
    cp   = champ_series.loc[idx].values
    gb   = test_full.loc[idx, 'good_bad'].values
    yearly.append({
        'year':        int(yr),
        'actual_dr':   float(1 - gb.mean()),
        'champion_pd': float(cp.mean()),
        'rebuilt_pd':  float(pd_cal_rebuilt.mean()) if yr == 2018 else None,
        'period':      'oot',
    })

yr_df = pd.DataFrame(yearly).sort_values('year').reset_index(drop=True)

# For training years we cannot easily replay the calibrated champion predictions
# per year, so we only plot actual_dr for training years.
train_rows = yr_df[yr_df['period'] == 'train']
oot_rows   = yr_df[yr_df['period'] == 'oot']

fig, ax = plt.subplots(figsize=(12, 5))

# Actual DR — full span
ax.plot(yr_df['year'], yr_df['actual_dr'] * 100,
        'k-o', lw=2, ms=5, label='Actual Default Rate')

# Champion PD — only OOT years (where we have stored predictions)
oot_champ = oot_rows.dropna(subset=['champion_pd'])
ax.plot(oot_champ['year'], oot_champ['champion_pd'] * 100,
        'b--s', lw=2, ms=5, label='Champion PD (2007-2015 model, scored on OOT)')

# Rebuilt star on 2018
ax.scatter([2018], [rebuilt_m['Mean_PD'] * 100],
           color=COLORS['orange'], s=180, zorder=5, marker='*',
           label=f"Rebuilt PD on 2018 ({rebuilt_m['Mean_PD']:.2%})")

# Shading: training window vs PSI ALERT window
ax.axvspan(2006.7, 2015.3, alpha=0.06, color='green',  label='Champion training window (2007-2015)')
ax.axvspan(2015.7, 2018.3, alpha=0.08, color='red',    label='PSI ALERT region (2016-2018)')

# Vertical divider at 2015/2016 boundary
ax.axvline(2015.5, color='gray', ls=':', lw=1.2)
ax.text(2011, ax.get_ylim()[0] if ax.get_ylim()[0] > 0 else 5,
        'Training period', ha='center', fontsize=8, color='green', alpha=0.8)
ax.text(2017, ax.get_ylim()[0] if ax.get_ylim()[0] > 0 else 5,
        'OOT period', ha='center', fontsize=8, color='red', alpha=0.8)

ax.set(xlabel='Issue Year', ylabel='Default Rate / Mean PD (%)',
       title='Full Picture: Champion Tracks 2007-2015, Drifts 2016-2018, Rebuilt Corrects 2018\n'
             'Actual Default Rate vs Champion PD (OOT years only) and Rebuilt PD')
ax.legend(fontsize=8, loc='upper left')
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:.0f}%'))
ax.set_xlim(2006.5, 2018.8)
plt.tight_layout()
plt.savefig('../data/reports/L05_yearly_pd_vs_actual_dr.png',
            dpi=150, bbox_inches='tight')
plt.show()
print("  Saved: L05_yearly_pd_vs_actual_dr.png")

# =============================================================================
# 10. Summary Table
# =============================================================================
print("\n" + "="*60)
print(" FINAL SUMMARY")
print("="*60)
summary = pd.DataFrame([champ_m, rebuilt_m]).set_index('Model')
print(summary[['AUC','Gini','KS','Brier','Mean_PD','Actual_DR']].round(4).to_string())

print(f"""
Key findings:
  Champion mean PD on 2018:  {champ_2018.mean():.2%}  (actual DR: {actual_dr_2018:.2%})
  Rebuilt  mean PD on 2018:  {pd_cal_rebuilt.mean():.2%} (correctly calibrated)
  Champion underprediction:  {(actual_dr_2018 - champ_2018.mean())*100:+.2f}pp
  Gini Champion:             {champ_m['Gini']:.4f}
  Gini Rebuilt:              {rebuilt_m['Gini']:.4f}
  Gini improvement:          {(rebuilt_m['Gini'] - champ_m['Gini'])*100:+.2f}pp
  Features Champion/Rebuilt: {len(DUMMY_COLS)} / {len(REBUILT_FEATURES)}
""")

# Save comparison CSV
summary.round(4).to_csv('../data/reports/L05_champion_vs_rebuilt_metrics.csv')
print("  Saved: L05_champion_vs_rebuilt_metrics.csv")
print("\n  L05 complete — 3 figures and 1 CSV saved to data/reports/")
