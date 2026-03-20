"""
NSAP Synthetic Dataset Generator
=================================
Generates a synthetic dataset for NSAP scheme eligibility classification.
Schemes: OAP, WP, DP, NOT_ELIGIBLE

Requirements: pandas, numpy (pip install pandas numpy)

Usage:
    python generate_nsap_dataset.py
    python generate_nsap_dataset.py --records 15000 --output my_dataset.csv --noise 0.07
"""

import pandas as pd
import numpy as np
import random
import argparse
import os

# ── Configuration ─────────────────────────────────────────────
SEED             = 42
TOTAL_RECORDS    = 15_000
BPL_THRESHOLD    = 72_000       # Annual income ceiling for BPL (INR)
LABEL_NOISE_RATE = 0.07         # 7% random label flips to simulate real-world errors
BOUNDARY_RATIO   = 0.18         # 18% records near eligibility boundaries
PRIORITY_ORDER   = ['WP', 'DP', 'OAP', 'NOT_ELIGIBLE']

# ── State demographic profiles ─────────────────────────────────
STATES = {
    'Uttar Pradesh':  {'weight': 0.18, 'urban_ratio': 0.22, 'income_factor': 0.85},
    'Bihar':          {'weight': 0.12, 'urban_ratio': 0.11, 'income_factor': 0.75},
    'Madhya Pradesh': {'weight': 0.08, 'urban_ratio': 0.27, 'income_factor': 0.82},
    'Rajasthan':      {'weight': 0.07, 'urban_ratio': 0.24, 'income_factor': 0.88},
    'West Bengal':    {'weight': 0.07, 'urban_ratio': 0.31, 'income_factor': 0.90},
    'Maharashtra':    {'weight': 0.06, 'urban_ratio': 0.45, 'income_factor': 1.10},
    'Odisha':         {'weight': 0.05, 'urban_ratio': 0.16, 'income_factor': 0.80},
    'Jharkhand':      {'weight': 0.05, 'urban_ratio': 0.24, 'income_factor': 0.78},
    'Assam':          {'weight': 0.04, 'urban_ratio': 0.14, 'income_factor': 0.82},
    'Andhra Pradesh': {'weight': 0.04, 'urban_ratio': 0.29, 'income_factor': 0.92},
    'Tamil Nadu':     {'weight': 0.04, 'urban_ratio': 0.48, 'income_factor': 1.05},
    'Karnataka':      {'weight': 0.04, 'urban_ratio': 0.38, 'income_factor': 1.00},
    'Gujarat':        {'weight': 0.03, 'urban_ratio': 0.42, 'income_factor': 1.08},
    'Chhattisgarh':   {'weight': 0.03, 'urban_ratio': 0.23, 'income_factor': 0.80},
    'Other':          {'weight': 0.10, 'urban_ratio': 0.30, 'income_factor': 0.90},
}

DISABILITY_TYPES = [
    'Locomotor', 'Visual', 'Hearing', 'Mental Illness',
    'Intellectual', 'Multiple Disabilities', 'Cerebral Palsy',
]

SOCIAL_WEIGHTS = {'SC': 0.25, 'ST': 0.15, 'OBC': 0.40, 'General': 0.20}

# Noise map: realistic bureaucratic misclassification patterns
CONFUSION_MAP = {
    'OAP':          ['NOT_ELIGIBLE', 'WP'],
    'WP':           ['OAP', 'NOT_ELIGIBLE'],
    'DP':           ['NOT_ELIGIBLE', 'OAP'],
    'NOT_ELIGIBLE': ['OAP', 'WP', 'DP'],
}


# ── Utility samplers ───────────────────────────────────────────
def pick_state():
    s = list(STATES.keys())
    w = [STATES[x]['weight'] for x in s]
    return np.random.choice(s, p=w)

def pick_social():
    return np.random.choice(
        list(SOCIAL_WEIGHTS.keys()),
        p=list(SOCIAL_WEIGHTS.values())
    )

def get_area(state):
    return 'Urban' if np.random.random() < STATES[state]['urban_ratio'] else 'Rural'

def income_bpl(state):
    """Triangular distribution clustered near BPL threshold — many borderline incomes."""
    return int(
        np.random.triangular(10_000, 45_000, BPL_THRESHOLD + 15_000)
        * STATES[state]['income_factor']
    )

def income_above(state):
    return int(
        np.random.triangular(BPL_THRESHOLD + 1000, 1_50_000, 5_00_000)
        * STATES[state]['income_factor']
    )

def rand_aadhaar(): return 'Yes' if np.random.random() < 0.91 else 'No'
def rand_bank():    return 'Yes' if np.random.random() < 0.88 else 'No'


# ── Deterministic label (pure rule-based ground truth) ─────────
def true_label(row):
    """
    NSAP eligibility rules (priority: WP > DP > OAP > NOT_ELIGIBLE):
      OAP : age >= 60 AND bpl_card == Yes
      WP  : Female, Widowed, age 40-79, bpl_card == Yes
      DP  : has_disability == Yes, disability% >= 40, age 18-79, bpl_card == Yes
    """
    qualifies = []
    if row['age'] >= 60 and row['bpl_card'] == 'Yes':
        qualifies.append('OAP')
    if (row['gender'] == 'Female' and row['marital_status'] == 'Widowed'
            and 40 <= row['age'] <= 79 and row['bpl_card'] == 'Yes'):
        qualifies.append('WP')
    if (row['has_disability'] == 'Yes' and row['disability_percentage'] >= 40
            and 18 <= row['age'] <= 79 and row['bpl_card'] == 'Yes'):
        qualifies.append('DP')
    for scheme in PRIORITY_ORDER:
        if scheme in qualifies:
            return scheme
    return 'NOT_ELIGIBLE'

def apply_noise(label):
    """Randomly flip labels at LABEL_NOISE_RATE to simulate data-entry errors."""
    if np.random.random() < LABEL_NOISE_RATE:
        return np.random.choice(CONFUSION_MAP[label])
    return label


# ── Profile builders (one per scheme type) ────────────────────
def oap_profile(state):
    g   = np.random.choice(['Male', 'Female'], p=[0.45, 0.55])
    wid = (g == 'Female' and np.random.random() < 0.55) or \
          (g == 'Male'   and np.random.random() < 0.18)
    hd  = np.random.random() < 0.12
    return {
        'age':                   int(np.random.triangular(60, 68, 90)),
        'gender':                g,
        'marital_status':        'Widowed' if wid else
                                 np.random.choice(['Married','Single','Divorced'], p=[0.65,0.25,0.10]),
        'annual_income':         income_bpl(state),
        'bpl_card':              'Yes',
        'area_type':             get_area(state),
        'social_category':       pick_social(),
        'employment_status':     np.random.choice(
                                     ['Unemployed','Self-employed','Agricultural Labour','Daily Wage'],
                                     p=[0.55,0.25,0.12,0.08]),
        'has_disability':        'Yes' if hd else 'No',
        'disability_percentage': int(np.random.uniform(5, 35)) if hd else 0,
        'disability_type':       np.random.choice(DISABILITY_TYPES) if hd else 'None',
        'aadhaar_linked':        rand_aadhaar(),
        'bank_account':          rand_bank(),
    }

def wp_profile(state):
    hd = np.random.random() < 0.09
    return {
        'age':                   int(np.random.triangular(40, 52, 79)),
        'gender':                'Female',
        'marital_status':        'Widowed',
        'annual_income':         income_bpl(state),
        'bpl_card':              'Yes',
        'area_type':             get_area(state),
        'social_category':       pick_social(),
        'employment_status':     np.random.choice(
                                     ['Unemployed','Self-employed','Agricultural Labour','Daily Wage'],
                                     p=[0.58,0.22,0.12,0.08]),
        'has_disability':        'Yes' if hd else 'No',
        'disability_percentage': int(np.random.uniform(5, 35)) if hd else 0,
        'disability_type':       np.random.choice(DISABILITY_TYPES) if hd else 'None',
        'aadhaar_linked':        rand_aadhaar(),
        'bank_account':          rand_bank(),
    }

def dp_profile(state):
    g = np.random.choice(['Male','Female'], p=[0.55,0.45])
    m = 'Widowed' if (g == 'Female' and np.random.random() < 0.18) else \
        np.random.choice(['Single','Married','Divorced','Widowed'], p=[0.35,0.50,0.08,0.07])
    return {
        'age':                   int(np.random.triangular(18, 38, 79)),
        'gender':                g,
        'marital_status':        m,
        'annual_income':         income_bpl(state),
        'bpl_card':              'Yes',
        'area_type':             get_area(state),
        'social_category':       pick_social(),
        'employment_status':     np.random.choice(
                                     ['Unemployed','Self-employed','Daily Wage'],
                                     p=[0.68,0.22,0.10]),
        'has_disability':        'Yes',
        'disability_percentage': int(np.random.triangular(40, 60, 100)),
        'disability_type':       np.random.choice(DISABILITY_TYPES),
        'aadhaar_linked':        rand_aadhaar(),
        'bank_account':          rand_bank(),
    }

def not_eligible_profile(state):
    """Five sub-types covering realistic rejection reasons."""
    g     = np.random.choice(['Male','Female'])
    vtype = np.random.choice(
        ['young', 'income_high', 'no_bpl', 'not_widowed', 'low_dis'],
        p=[0.28, 0.22, 0.20, 0.15, 0.15],
    )
    base = {
        'area_type':       get_area(state),
        'social_category': pick_social(),
        'aadhaar_linked':  rand_aadhaar(),
        'bank_account':    rand_bank(),
    }
    extras = {
        'young':       {'age': int(np.random.triangular(18,35,55)), 'gender': g,
                        'marital_status': 'Single', 'annual_income': income_bpl(state),
                        'bpl_card': 'Yes', 'employment_status': 'Unemployed',
                        'has_disability': 'No', 'disability_percentage': 0,
                        'disability_type': 'None'},
        'income_high': {'age': int(np.random.triangular(45,65,85)), 'gender': g,
                        'marital_status': 'Married', 'annual_income': income_above(state),
                        'bpl_card': 'No', 'employment_status': 'Salaried',
                        'has_disability': 'No', 'disability_percentage': 0,
                        'disability_type': 'None'},
        'no_bpl':      {'age': int(np.random.triangular(55,68,85)), 'gender': g,
                        'marital_status': 'Married', 'annual_income': income_bpl(state),
                        'bpl_card': 'No', 'employment_status': 'Agricultural Labour',
                        'has_disability': 'No', 'disability_percentage': 0,
                        'disability_type': 'None'},
        'not_widowed': {'age': int(np.random.triangular(30,45,60)), 'gender': 'Female',
                        'marital_status': 'Married', 'annual_income': income_bpl(state),
                        'bpl_card': 'Yes', 'employment_status': 'Unemployed',
                        'has_disability': 'No', 'disability_percentage': 0,
                        'disability_type': 'None'},
        'low_dis':     {'age': int(np.random.triangular(20,40,70)), 'gender': g,
                        'marital_status': 'Single', 'annual_income': income_bpl(state),
                        'bpl_card': 'Yes', 'employment_status': 'Unemployed',
                        'has_disability': 'Yes',
                        'disability_percentage': int(np.random.uniform(5, 39)),
                        'disability_type': np.random.choice(DISABILITY_TYPES)},
    }
    base.update(extras[vtype])
    return base

def boundary_profile(state):
    """Records near decision boundaries — genuinely ambiguous cases."""
    btype = np.random.choice(
        ['age_oap', 'age_wp', 'income', 'disability', 'multi'],
        p=[0.25, 0.20, 0.25, 0.20, 0.10],
    )
    g    = np.random.choice(['Male', 'Female'])
    base = {
        'area_type':       get_area(state),
        'social_category': pick_social(),
        'aadhaar_linked':  rand_aadhaar(),
        'bank_account':    rand_bank(),
    }

    if btype == 'age_oap':      # age 57-63: straddles OAP threshold of 60
        base.update({'age': int(np.random.uniform(57, 63)), 'gender': g,
                     'marital_status': np.random.choice(['Married','Single','Widowed'], p=[0.5,0.3,0.2]),
                     'annual_income': income_bpl(state), 'bpl_card': 'Yes',
                     'employment_status': 'Unemployed',
                     'has_disability': 'No', 'disability_percentage': 0, 'disability_type': 'None'})

    elif btype == 'age_wp':     # age 37-43: straddles WP lower threshold of 40
        base.update({'age': int(np.random.uniform(37, 43)), 'gender': 'Female',
                     'marital_status': 'Widowed', 'annual_income': income_bpl(state),
                     'bpl_card': 'Yes', 'employment_status': 'Unemployed',
                     'has_disability': 'No', 'disability_percentage': 0, 'disability_type': 'None'})

    elif btype == 'income':     # income ±8k around BPL_THRESHOLD
        inc = int(np.random.uniform(BPL_THRESHOLD - 8000, BPL_THRESHOLD + 8000))
        base.update({'age': int(np.random.triangular(55, 67, 80)), 'gender': g,
                     'marital_status': np.random.choice(['Married','Widowed'], p=[0.6,0.4]),
                     'annual_income': inc, 'bpl_card': 'Yes' if inc < BPL_THRESHOLD else 'No',
                     'employment_status': 'Agricultural Labour',
                     'has_disability': 'No', 'disability_percentage': 0, 'disability_type': 'None'})

    elif btype == 'disability': # disability% 34-46: straddles DP threshold of 40%
        base.update({'age': int(np.random.triangular(20, 40, 70)), 'gender': g,
                     'marital_status': np.random.choice(['Single','Married'], p=[0.5,0.5]),
                     'annual_income': income_bpl(state), 'bpl_card': 'Yes',
                     'employment_status': 'Unemployed',
                     'has_disability': 'Yes',
                     'disability_percentage': int(np.random.uniform(34, 46)),
                     'disability_type': np.random.choice(DISABILITY_TYPES)})

    else:                       # multi: qualifies for several schemes simultaneously
        base.update({'age': int(np.random.uniform(60, 75)), 'gender': 'Female',
                     'marital_status': 'Widowed', 'annual_income': income_bpl(state),
                     'bpl_card': 'Yes', 'employment_status': 'Unemployed',
                     'has_disability': 'Yes',
                     'disability_percentage': int(np.random.uniform(40, 70)),
                     'disability_type': np.random.choice(DISABILITY_TYPES)})
    return base


# ── Main generation function ───────────────────────────────────
def generate_dataset(total_records=TOTAL_RECORDS, noise_rate=LABEL_NOISE_RATE,
                     boundary_ratio=BOUNDARY_RATIO, seed=SEED):

    np.random.seed(seed)
    random.seed(seed)

    n_boundary = int(total_records * boundary_ratio)
    n_core     = total_records - n_boundary

    dist_cfg = {'OAP': 0.52, 'WP': 0.17, 'DP': 0.06, 'NOT_ELIGIBLE': 0.25}
    gen_map  = {
        'OAP': oap_profile, 'WP': wp_profile,
        'DP': dp_profile, 'NOT_ELIGIBLE': not_eligible_profile
    }

    records = []

    counts = {cls: int(n_core * r) for cls, r in dist_cfg.items()}
    counts['OAP'] += n_core - sum(counts.values())  # absorb rounding remainder

    for cls, count in counts.items():
        for _ in range(count):
            state = pick_state()
            rec   = gen_map[cls](state)
            rec['state'] = state
            records.append(rec)

    for _ in range(n_boundary):
        state = pick_state()
        rec   = boundary_profile(state)
        rec['state'] = state
        records.append(rec)

    df = pd.DataFrame(records).sample(frac=1, random_state=seed).reset_index(drop=True)

    # Apply deterministic labels then noise
    df['primary_scheme'] = df.apply(true_label, axis=1)
    df['primary_scheme'] = df['primary_scheme'].apply(
        lambda lbl: np.random.choice(CONFUSION_MAP[lbl]) if np.random.random() < noise_rate else lbl
    )

    # Add applicant IDs
    df.insert(0, 'applicant_id', [f'NSAP{str(i).zfill(6)}' for i in range(1, len(df)+1)])

    # Feature engineering (mirrors Section 5 of training notebook)
    df['age_x_disability_pct'] = df['age'] * df['disability_percentage'] / 100
    df['income_to_bpl_ratio']  = df['annual_income'] / BPL_THRESHOLD
    df['is_widowed_female']    = (
        (df['gender'] == 'Female') & (df['marital_status'] == 'Widowed')
    ).astype(int)

    return df


# ── CLI entry point ────────────────────────────────────────────
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate NSAP synthetic dataset')
    parser.add_argument('--records',  type=int,   default=15000,
                        help='Total number of records (default: 15000)')
    parser.add_argument('--output',   type=str,   default='nsap_synthetic_dataset.csv',
                        help='Output CSV filename (default: nsap_synthetic_dataset.csv in sample_data)')
    parser.add_argument('--noise',    type=float, default=0.07,
                        help='Label noise rate 0.0-1.0 (default: 0.07)')
    parser.add_argument('--boundary', type=float, default=0.18,
                        help='Boundary record ratio 0.0-1.0 (default: 0.18)')
    parser.add_argument('--seed',     type=int,   default=42,
                        help='Random seed for reproducibility (default: 42)')
    args = parser.parse_args()

    print(f'Generating {args.records:,} records...')
    print(f'  Label noise rate : {args.noise*100:.0f}%')
    print(f'  Boundary ratio   : {args.boundary*100:.0f}%')
    print(f'  Random seed      : {args.seed}')

    df = generate_dataset(
        total_records=args.records,
        noise_rate=args.noise,
        boundary_ratio=args.boundary,
        seed=args.seed
    )

    # Save dataset to sample_data/ folder at project root
    # Navigate from ml/ up to project root then into sample_data/
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sample_data_dir = os.path.join(project_root, "sample_data")
    output_file = os.path.basename(args.output)
    output_path = os.path.join(sample_data_dir, output_file)
    os.makedirs(sample_data_dir, exist_ok=True)
    df.to_csv(output_path, index=False)

    print(f'\nDataset saved to: {output_path}')
    print(f'Shape            : {df.shape[0]:,} rows x {df.shape[1]} columns')
    print(f'\nClass distribution:')
    for cls, cnt in df['primary_scheme'].value_counts().items():
        print(f'  {cls:<15}: {cnt:>5} ({cnt/len(df)*100:.1f}%)')
    print(f'\nColumns: {list(df.columns)}')