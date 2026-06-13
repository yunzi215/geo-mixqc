"""GEO-MixQC core: mixed-normalization detection engine"""
import gzip, warnings
import numpy as np
from scipy import stats
from scipy.cluster.vq import kmeans2
from scipy.cluster.hierarchy import linkage, fcluster

warnings.filterwarnings("ignore")

# ═══════════════════════════════════════
# Matrix I/O
# ═══════════════════════════════════════

def load_matrix(path):
    """Load a GEO Series Matrix file (.txt or .txt.gz).
    
    Returns: (expr_array, platform_string, dimensions_string)
    """
    with open(path, "rb") as f:
        raw = f.read()
    
    try:
        content = gzip.decompress(raw).decode("utf-8", errors="replace")
    except:
        content = raw.decode("utf-8", errors="replace")
    
    idx = content.find("!series_matrix_table_begin")
    if idx < 0:
        return None, None, "NO_MATRIX_TABLE"
    
    # Parse platform
    platform = "Unknown"
    for line in content[:idx].split("\n"):
        if line.startswith("!Series_platform_id"):
            platform = line.split("=")[-1].strip().strip('"')
            break
    
    # Parse expression values
    tbl = content[idx + len("!series_matrix_table_begin"):].strip()
    lines = [l for l in tbl.split("\n") if l.strip()]
    if len(lines) < 2:
        return None, platform, "EMPTY_TABLE"
    
    nc = len(lines[0].strip().split("\t")) - 1
    if nc < 2:
        return None, platform, f"TOO_FEW_COLS({nc})"
    nr = len(lines) - 1
    
    vals = []
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        p = line.split("\t")
        if len(p) < 2:
            continue
        row = [np.nan] * nc
        limit = min(len(p), nc + 1)
        for j in range(1, limit):
            try:
                row[j - 1] = float(p[j].strip('"'))
            except:
                pass
        vals.append(row)
    
    if not vals:
        return None, platform, "NO_DATA_ROWS"
    
    expr = np.array(vals, dtype=np.float64)
    if expr.ndim == 1:
        return None, platform, f"SINGLE_ROW({len(vals)})"
    
    return expr, platform, f"{nr} rows x {nc} cols"


# ═══════════════════════════════════════
# Five-test scoring engine
# ═══════════════════════════════════════

def _score_mixed_normalization(expr):
    """T1: Score 0-100 for mixed-normalization artifacts using five sub-tests."""
    valid = ~np.all(np.isnan(expr), axis=0)
    expr = expr[:, valid]
    ns = expr.shape[1]
    if ns < 15:
        return {"score": 0, "level": "INSUFFICIENT_SAMPLES", "ns": ns, "flags": {}}
    
    med = np.nanmedian(expr, axis=0)
    mx = np.nanmax(expr, axis=0)
    mn = np.nanmin(expr, axis=0)
    iqr = np.percentile(expr, 75, axis=0) - np.percentile(expr, 25, axis=0)
    
    v = ~np.isnan(med)
    med, mx, mn, iqr = med[v], mx[v], mn[v], iqr[v]
    
    score = 0
    flags = {}
    
    # T1 - Bimodal sample median
    lm = np.log2(np.clip(med, 1, np.inf))
    try:
        _, labs = kmeans2(lm.reshape(-1, 1), k=2, minit="points")
        d = abs(np.mean(lm[labs == 0]) - np.mean(lm[labs == 1]))
        n0, n1 = sum(labs == 0), sum(labs == 1)
        if d > 2 and n0 / ns > 0.2 and n1 / ns > 0.2:
            flags["bimodal_median"] = f"{d:.1f} log2 ({n0}/{n1} samples)"
            score += 30
    except:
        pass
    
    # T2 - Mixed expression scale
    p_lin = np.mean(mx > 100)
    p_log = np.mean(mx < 20)
    if 0.15 < p_lin < 0.85:
        flags["mixed_scale"] = f"linear={p_lin:.0%}, log2={p_log:.0%}"
        score += 25
    
    # T3 - Negative value inconsistency
    p_neg = np.mean(mn < 0)
    if 0.1 < p_neg < 0.9 and p_lin > 0.1:
        flags["mixed_negative"] = f"{p_neg:.0%} samples have negative values"
        score += 15
    
    # T4 - IQR/median ratio instability
    ratio = iqr / np.clip(med, 0.01, np.inf)
    cv = np.std(ratio) / (np.mean(ratio) + 1e-10)
    if cv > 1.5:
        flags["iqr_ratio_cv"] = f"CV={cv:.2f}"
        score += 10
    
    # T5 - Scale-driven hierarchical clustering
    try:
        X = np.column_stack([med / np.std(med), np.log1p(mx) / np.std(np.log1p(mx))])
        Z = linkage(X, method="ward")
        labs = fcluster(Z, t=2, criterion="maxclust")
        d = abs(np.log2(np.mean(med[labs == 1]) + 1) - np.log2(np.mean(med[labs == 2]) + 1))
        if d > 3:
            flags["clustering_by_scale"] = f"{d:.1f} log2 separation"
            score += 20
    except:
        pass
    
    score = min(score, 100)
    level = "HIGH" if score >= 50 else ("MEDIUM" if score >= 20 else "LOW")
    return {"score": score, "level": level, "ns": ns, "flags": flags}


def run_all_tests(expr, platform="Unknown"):
    """Run the complete GEO-MixQC test suite on an expression matrix.
    
    Args:
        expr: numpy array (probes x samples)
        platform: declared GEO platform ID (e.g., 'GPL570')
    
    Returns:
        dict with risk_score, risk_level, test_details, and verdict
    """
    result = {}
    
    # Core test: mixed normalization detection
    t1 = _score_mixed_normalization(expr)
    result["risk_score"] = t1["score"]
    result["risk_level"] = t1["level"]
    
    # Build detailed per-test report
    result["tests"] = []
    flags = t1.get("flags", {})
    
    if "bimodal_median" in flags:
        result["tests"].append({"test": "T1_bimodal_median", "score": 30, "details": flags["bimodal_median"]})
    else:
        result["tests"].append({"test": "T1_bimodal_median", "score": 0, "details": "No bimodal separation detected"})
    
    if "mixed_scale" in flags:
        result["tests"].append({"test": "T2_mixed_scale", "score": 25, "details": flags["mixed_scale"]})
    else:
        result["tests"].append({"test": "T2_mixed_scale", "score": 0, "details": "Consistent expression scale"})
    
    if "mixed_negative" in flags:
        result["tests"].append({"test": "T3_negative_inconsistency", "score": 15, "details": flags["mixed_negative"]})
    else:
        result["tests"].append({"test": "T3_negative_inconsistency", "score": 0, "details": "No negative value inconsistency"})
    
    if "iqr_ratio_cv" in flags:
        result["tests"].append({"test": "T4_iqr_instability", "score": 10, "details": flags["iqr_ratio_cv"]})
    else:
        result["tests"].append({"test": "T4_iqr_instability", "score": 0, "details": "Stable IQR/median ratios"})
    
    if "clustering_by_scale" in flags:
        result["tests"].append({"test": "T5_scale_clustering", "score": 20, "details": flags["clustering_by_scale"]})
    else:
        result["tests"].append({"test": "T5_scale_clustering", "score": 0, "details": "No scale-driven clustering"})
    
    # Platform
    result["platform"] = platform
    
    # Verdict
    if result["risk_level"] == "HIGH":
        result["verdict"] = "CRITICAL: Mixed normalization detected. Do NOT pool samples without stratification."
    elif result["risk_level"] == "MEDIUM":
        result["verdict"] = "WARNING: Possible mixed normalization. Manual review of sample statistics recommended."
    else:
        result["verdict"] = "PASS: No mixed normalization detected."
    
    return result
