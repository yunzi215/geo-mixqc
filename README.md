# GEO-MixQC: Mixed-Normalization Detector for Public Transcriptomic Matrices

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-%E2%89%A53.8-blue)](https://python.org)
[![DOI](https://zenodo.org/badge/DOI/placeholder.svg)](https://doi.org/placeholder)

**A five-test algorithm that screens GEO Series Matrix files for hidden mixed-normalization artifacts before downstream analysis.**

## Overview

Public transcriptomic repositories (GEO, ArrayExpress) are widely reused for secondary analysis. However, deposited processed matrices may silently contain samples normalized by **different methods** within a single file — for example, RMA (log2-scale) and dChip (linear-scale). Naive pooled analysis of such matrices yields results overwhelmingly driven by preprocessing artifacts.

**GEO-MixQC** provides a lightweight, zero-configuration screening tool that analyzes a Series Matrix file and returns a 0-100 risk score.

### Key Features
- **Five independent tests** targeting distinct signatures of mixed preprocessing
- **Zero configuration** — just point to a `.txt.gz` file
- **Interpretable output** — JSON report with per-test diagnostics
- **Batch mode** — screen hundreds of datasets in parallel
- **Fast** — <5 seconds per dataset (2,000-probe subset)

## Installation

```bash
# From PyPI (coming soon)
pip install geo-mixqc

# From GitHub
git clone https://github.com/YOUR_USERNAME/geo-mixqc.git
cd geo-mixqc
pip install -e .
```

Requirements: Python >= 3.8, NumPy >= 1.20, SciPy >= 1.7

## Quick Start

```bash
# Single file
geo-mixqc GSE26049_series_matrix.txt.gz

# JSON output for downstream processing
geo-mixqc --json GSE26049_series_matrix.txt.gz

# Batch mode: process all .gz files in a directory
geo-mixqc --batch /path/to/matrices/
```

### Example Output

```json
{
  "file": "GSE26049_series_matrix.txt.gz",
  "dimensions": "54675 rows x 181 cols",
  "platform": "GPL570",
  "T1_bimodal_median": {"score": 30, "details": "delta=4.1 log2 (91/90 samples)"},
  "T2_mixed_scale": {"score": 25, "details": "linear=49.7%, log2=50.3%"},
  "T3_negative_inconsistency": {"score": 0},
  "T4_iqr_instability": {"score": 0},
  "T5_scale_clustering": {"score": 20, "details": "3.9 log2 separation"},
  "risk_score": 75,
  "risk_level": "HIGH",
  "verdict": "CRITICAL: Mixed normalization detected"
}
```

## The Five Tests

| Test | What it detects | Score |
|------|----------------|-------|
| **T1** Bimodal median | log2(sample median) forms two distinct clusters | +30 |
| **T2** Mixed scale | Samples span both log2 (<20) and linear (>100) ranges | +25 |
| **T3** Negative values | Some samples have negative values, others don't | +15 |
| **T4** IQR instability | CV of IQR/median ratio exceeds 1.5 across samples | +10 |
| **T5** Scale clustering | Samples cluster by expression scale, not biology | +20 |

**Risk levels**: HIGH (>=50), MEDIUM (20-49), LOW (<20)

## Background Scan Results

GEO-MixQC was validated on **550 GPL570** (Affymetrix HG-U133 Plus 2.0) Series Matrix files from GEO. Key findings:

- **0 HIGH-risk false positives** among 550 background datasets
- **3 MEDIUM-risk flags** (score=20, single-test triggers, biological heterogeneity)
- **GSE26049**: confirmed semi-silent mixed normalization (RMA + dChip co-deposited; 52,472/54,675 probes at FDR<0.05 when naively compared)
- **Estimated prevalence of mixed-normalization patterns among downloadable GPL570 matrices: <1%**

A companion metadata scan of **31,301** GEO expression array datasets is documented in the manuscript.

## Citation

If you use GEO-MixQC in your research, please cite:

```
Yun et al. GEO-MixQC: Detecting Mixed-Normalization Patterns in Public 
Transcriptomic Matrices. 2026. DOI: [to be assigned]
```

## Limitations

- Designed for **scale-discordant** mixtures (log2 vs linear). May not detect subtle normalization differences within the same numerical scale.
- Currently supports **microarray** Series Matrix files. RNA-seq support is planned.
- Not a replacement for raw-array QC or batch correction — it is a **pre-analysis screening tool**.

## License

MIT License. See [LICENSE](LICENSE) for details.

## Contributing

Issues and pull requests are welcome. Please include example matrix files (or links to public GEO datasets) when reporting detection issues.
