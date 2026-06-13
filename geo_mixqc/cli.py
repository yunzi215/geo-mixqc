#!/usr/bin/env python3
"""GEO-MixQC command-line interface"""
import sys, json, argparse
from geo_mixqc.core import load_matrix, run_all_tests

def main():
    parser = argparse.ArgumentParser(
        description="GEO-MixQC: Detect mixed-normalization artifacts in GEO Series Matrix files"
    )
    parser.add_argument("path", help="Path to Series Matrix file (.txt or .txt.gz)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--batch", help="Process all .txt.gz files in a directory")
    parser.add_argument("--version", action="version", version="geo-mixqc 1.0.0")
    args = parser.parse_args()
    
    if args.batch:
        import os, glob
        files = sorted(glob.glob(os.path.join(args.batch, "*.txt.gz")))
        if not files:
            print(f"No .txt.gz files found in {args.batch}", file=sys.stderr)
            sys.exit(1)
        results = []
        for f in files:
            expr, platform, dims = load_matrix(f)
            if expr is None:
                results.append({"file": os.path.basename(f), "error": dims})
            else:
                report = run_all_tests(expr, platform)
                report["file"] = os.path.basename(f)
                report["dimensions"] = dims
                results.append(report)
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            for r in results:
                print(f"{r['file']:40s} score={r.get('risk_score', 'ERR'):>3} {r.get('risk_level', 'ERROR')}")
        return
    
    expr, platform, dims = load_matrix(args.path)
    if expr is None:
        print(f"Error: {dims}", file=sys.stderr)
        sys.exit(1)
    
    report = run_all_tests(expr, platform)
    report["file"] = args.path
    report["dimensions"] = dims
    
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"\n{'='*60}")
        print(f"GEO-MixQC Report: {args.path}")
        print(f"{'='*60}")
        print(f"  Platform:   {report.get('platform', 'Unknown')}")
        print(f"  Dimensions: {report.get('dimensions', 'N/A')}")
        print(f"  Risk Score: {report['risk_score']}/100  [{report['risk_level']}]")
        print(f"\n  Test details:")
        for t in ['T1_bimodal_median','T2_mixed_scale','T3_negative_inconsistency',
                   'T4_iqr_instability','T5_scale_clustering']:
            ti = report.get(t, {})
            if ti:
                print(f"    {t[3:]}: score={ti.get('score',0)}, {ti.get('details','')}")
        print(f"\n  Verdict: {report['verdict']}")
        print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
