#!/usr/bin/env python3
"""
データベース実行計画JSON比較ツール
DeepDiffを使用して2つの実行計画を比較し、詳細な差分レポートを生成
"""

import json
from deepdiff import DeepDiff
from typing import Any, Dict, Optional
from datetime import datetime


# ============================================================
# ハードコーディングされたパラメータ
# ============================================================
PLAN1_PATH = "plan1.json"          # 基準となる実行計画ファイルパス
PLAN2_PATH = "plan2.json"          # 比較対象の実行計画ファイルパス
OUTPUT_PATH = "report.txt"         # テキストレポート出力パス（Noneで出力しない）
JSON_OUTPUT_PATH = "diff.json"     # JSON差分出力パス（Noneで出力しない）
IGNORE_ORDER = True                # リストの順序を無視するか
SIGNIFICANT_DIGITS = 2             # 数値比較の有効桁数
EXCLUDE_PATHS = []                 # 除外するパスのリスト
SHOW_METRICS = True                # キー指標の比較を表示するか


def load_json(file_path: str) -> Dict[str, Any]:
    """JSONファイルを読み込む"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def compare_execution_plans(
    plan1: Dict[str, Any],
    plan2: Dict[str, Any],
    ignore_order: bool = True,
    significant_digits: int = 2,
    exclude_paths: Optional[list] = None
) -> DeepDiff:
    """
    2つの実行計画を比較する
    
    引数:
        plan1: 最初の実行計画（基準）
        plan2: 2番目の実行計画（比較対象）
        ignore_order: リストの順序を無視するか
        significant_digits: 数値比較の有効桁数
        exclude_paths: 除外するパスのリスト
    
    戻り値:
        DeepDiffオブジェクト
    """
    exclude_paths = exclude_paths or []
    
    diff = DeepDiff(
        plan1,
        plan2,
        ignore_order=ignore_order,
        significant_digits=significant_digits,
        exclude_paths=exclude_paths,
        verbose_level=2,  # 詳細情報を表示
        view='tree'       # ツリービューで走査しやすくする
    )
    
    return diff


def format_diff_report(diff: DeepDiff, plan1_name: str, plan2_name: str) -> str:
    """
    差分レポートをフォーマットする
    
    引数:
        diff: DeepDiffオブジェクト
        plan1_name: 最初の計画の名前
        plan2_name: 2番目の計画の名前
    
    戻り値:
        フォーマットされたレポート文字列
    """
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("データベース実行計画比較レポート")
    report_lines.append("=" * 80)
    report_lines.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"基準計画: {plan1_name}")
    report_lines.append(f"比較計画: {plan2_name}")
    report_lines.append("-" * 80)
    
    if not diff:
        report_lines.append("\n✅ 2つの実行計画は完全に同一です。差分はありません。\n")
        return "\n".join(report_lines)
    
    # 1. 型の変更
    if 'type_changes' in diff:
        report_lines.append("\n📌 【型の変更】")
        report_lines.append("-" * 40)
        for item in diff['type_changes']:
            path = item.path()
            report_lines.append(f"  パス: {path}")
            report_lines.append(f"    旧型: {type(item.t1).__name__} -> 新型: {type(item.t2).__name__}")
            report_lines.append(f"    旧値: {item.t1}")
            report_lines.append(f"    新値: {item.t2}")
            report_lines.append("")
    
    # 2. 値の変更
    if 'values_changed' in diff:
        report_lines.append("\n📝 【値の変更】")
        report_lines.append("-" * 40)
        for item in diff['values_changed']:
            path = item.path()
            report_lines.append(f"  パス: {path}")
            report_lines.append(f"    旧値: {item.t1}")
            report_lines.append(f"    新値: {item.t2}")
            
            # 数値の変化の場合、変化率を計算
            if isinstance(item.t1, (int, float)) and isinstance(item.t2, (int, float)):
                if item.t1 != 0:
                    change_pct = ((item.t2 - item.t1) / item.t1) * 100
                    report_lines.append(f"    変化: {change_pct:+.2f}%")
            report_lines.append("")
    
    # 3. 追加項目
    if 'dictionary_item_added' in diff:
        report_lines.append("\n➕ 【追加項目】")
        report_lines.append("-" * 40)
        for item in diff['dictionary_item_added']:
            path = item.path()
            report_lines.append(f"  パス: {path}")
            report_lines.append(f"    値: {item.t2}")
            report_lines.append("")
    
    # 4. 削除項目
    if 'dictionary_item_removed' in diff:
        report_lines.append("\n➖ 【削除項目】")
        report_lines.append("-" * 40)
        for item in diff['dictionary_item_removed']:
            path = item.path()
            report_lines.append(f"  パス: {path}")
            report_lines.append(f"    値: {item.t1}")
            report_lines.append("")
    
    # 5. リスト項目の追加
    if 'iterable_item_added' in diff:
        report_lines.append("\n📋➕ 【リスト項目の追加】")
        report_lines.append("-" * 40)
        for item in diff['iterable_item_added']:
            path = item.path()
            report_lines.append(f"  パス: {path}")
            report_lines.append(f"    追加値: {item.t2}")
            report_lines.append("")
    
    # 6. リスト項目の削除
    if 'iterable_item_removed' in diff:
        report_lines.append("\n📋➖ 【リスト項目の削除】")
        report_lines.append("-" * 40)
        for item in diff['iterable_item_removed']:
            path = item.path()
            report_lines.append(f"  パス: {path}")
            report_lines.append(f"    削除値: {item.t1}")
            report_lines.append("")
    
    # 7. 重複項目の変化
    if 'repetition_change' in diff:
        report_lines.append("\n🔄 【重複項目の変化】")
        report_lines.append("-" * 40)
        for item in diff['repetition_change']:
            path = item.path()
            report_lines.append(f"  パス: {path}")
            report_lines.append(f"    詳細: {item}")
            report_lines.append("")
    
    # 統計サマリー
    report_lines.append("\n" + "=" * 80)
    report_lines.append("📊 差分統計サマリー")
    report_lines.append("=" * 80)
    
    stats = {
        '型の変更': len(diff.get('type_changes', [])),
        '値の変更': len(diff.get('values_changed', [])),
        '追加項目': len(diff.get('dictionary_item_added', [])),
        '削除項目': len(diff.get('dictionary_item_removed', [])),
        'リスト項目の追加': len(diff.get('iterable_item_added', [])),
        'リスト項目の削除': len(diff.get('iterable_item_removed', [])),
    }
    
    total = sum(stats.values())
    for name, count in stats.items():
        if count > 0:
            report_lines.append(f"  {name}: {count}")
    
    report_lines.append(f"\n  差分の総数: {total}")
    report_lines.append("=" * 80)
    
    return "\n".join(report_lines)


def extract_key_metrics(plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    実行計画からキー指標を抽出（一般的なデータベース形式に対応）
    
    対応形式:
    - PostgreSQL EXPLAIN (JSON)
    - MySQL EXPLAIN (JSON)
    - Oracle 実行計画
    """
    metrics = {}
    
    # PostgreSQL形式
    if isinstance(plan, list) and len(plan) > 0 and 'Plan' in plan[0]:
        pg_plan = plan[0]['Plan']
        metrics['total_cost'] = pg_plan.get('Total Cost', 'N/A')
        metrics['startup_cost'] = pg_plan.get('Startup Cost', 'N/A')
        metrics['plan_rows'] = pg_plan.get('Plan Rows', 'N/A')
        metrics['plan_width'] = pg_plan.get('Plan Width', 'N/A')
        metrics['node_type'] = pg_plan.get('Node Type', 'N/A')
        
        # 実行時間情報（ある場合）
        if 'Execution Time' in plan[0]:
            metrics['execution_time'] = plan[0]['Execution Time']
        if 'Planning Time' in plan[0]:
            metrics['planning_time'] = plan[0]['Planning Time']
    
    # MySQL形式
    elif 'query_block' in plan:
        qb = plan['query_block']
        if 'cost_info' in qb:
            metrics['query_cost'] = qb['cost_info'].get('query_cost', 'N/A')
        if 'table' in qb:
            table = qb['table']
            metrics['access_type'] = table.get('access_type', 'N/A')
            metrics['rows_examined'] = table.get('rows_examined_per_scan', 'N/A')
            metrics['filtered'] = table.get('filtered', 'N/A')
    
    # 汎用的な抽出
    else:
        # 一般的なフィールドの抽出を試みる
        common_fields = ['cost', 'rows', 'time', 'type', 'operation']
        for field in common_fields:
            if field in plan:
                metrics[field] = plan[field]
    
    return metrics


def compare_key_metrics(plan1: Dict[str, Any], plan2: Dict[str, Any]) -> str:
    """2つの実行計画のキー指標を比較"""
    metrics1 = extract_key_metrics(plan1)
    metrics2 = extract_key_metrics(plan2)
    
    if not metrics1 and not metrics2:
        return "キー指標を抽出できません（サポートされていない実行計画形式の可能性があります）"
    
    lines = []
    lines.append("\n📈 キー指標の比較")
    lines.append("-" * 40)
    
    all_keys = set(metrics1.keys()) | set(metrics2.keys())
    
    for key in sorted(all_keys):
        val1 = metrics1.get(key, 'N/A')
        val2 = metrics2.get(key, 'N/A')
        
        status = "✓" if val1 == val2 else "✗"
        lines.append(f"  {status} {key}:")
        lines.append(f"      基準: {val1}")
        lines.append(f"      比較: {val2}")
        
        # 数値変化を計算
        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            diff = val2 - val1
            if val1 != 0:
                pct = (diff / val1) * 100
                trend = "📈" if diff > 0 else "📉" if diff < 0 else "➡️"
                lines.append(f"      変化: {diff:+.2f} ({pct:+.2f}%) {trend}")
    
    return "\n".join(lines)


def main():
    """メイン関数"""
    
    # JSONファイルを読み込む
    try:
        plan1 = load_json(PLAN1_PATH)
        plan2 = load_json(PLAN2_PATH)
    except FileNotFoundError as e:
        print(f"❌ エラー: ファイルが見つかりません - {e}")
        return 1
    except json.JSONDecodeError as e:
        print(f"❌ エラー: JSON解析に失敗しました - {e}")
        return 1
    
    # 比較を実行
    diff = compare_execution_plans(
        plan1,
        plan2,
        ignore_order=IGNORE_ORDER,
        significant_digits=SIGNIFICANT_DIGITS,
        exclude_paths=EXCLUDE_PATHS
    )
    
    # レポートを生成
    report = format_diff_report(diff, PLAN1_PATH, PLAN2_PATH)
    
    # キー指標の比較を追加
    if SHOW_METRICS:
        report += "\n" + compare_key_metrics(plan1, plan2)
    
    # レポートを出力
    print(report)
    
    # テキストレポートを保存
    if OUTPUT_PATH:
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n📄 レポートを保存しました: {OUTPUT_PATH}")
    
    # JSON形式の差分を保存
    if JSON_OUTPUT_PATH:
        # シリアライズ可能な形式に変換
        diff_text = DeepDiff(
            plan1, plan2,
            ignore_order=IGNORE_ORDER,
            significant_digits=SIGNIFICANT_DIGITS,
            exclude_paths=EXCLUDE_PATHS
        ).to_json()
        
        with open(JSON_OUTPUT_PATH, 'w', encoding='utf-8') as f:
            f.write(diff_text)
        print(f"📄 JSON差分を保存しました: {JSON_OUTPUT_PATH}")
    
    return 0 if not diff else 1


if __name__ == '__main__':
    exit(main())
