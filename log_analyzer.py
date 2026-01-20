#!/usr/bin/env python3
"""
Log Analyzer for specified module
Parses log files to calculate execution time for each function per Pref Cd.

Usage:
    python log_analyzer.py <module_name> <input_log_file> <output_csv_file>

Example:
    python log_analyzer.py FORM_LONG_TERM_CARE_FACILITY log log_analysis_result.csv
"""

import re
import csv
import sys
import os
from datetime import datetime
from dataclasses import dataclass


@dataclass
class FunctionRecord:
    """Record of a function execution."""
    pref_cd: str
    function: str
    start_time: str
    end_time: str
    duration_sec: float


def parse_timestamp(ts_str: str) -> datetime:
    """Parse timestamp string to datetime object."""
    return datetime.strptime(ts_str.strip(), "%Y-%m-%d %H:%M:%S.%f")


def parse_log_line(line: str, target_module: str) -> dict | None:
    """
    Parse a single log line and extract relevant information.
    Returns dict with timestamp, module, function_name, action (Start/End), pref_cd if applicable.
    """
    # Pattern for function start/end lines
    # Format: TIMESTAMP,[TIMESTAMP2] [TableauFeedback] [MODULE] Start/End Function : function_name()
    func_pattern = r'^[\d\-:\s\.]+,(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+) \[TableauFeedback\] \[(\w+)\] (Start|End) Function : (\w+)\(\)'
    
    # Pattern for Pref Cd lines
    pref_pattern = r'^[\d\-:\s\.]+,(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+) \[TableauFeedback\] Pref Cd : (\d+)'
    
    func_match = re.match(func_pattern, line)
    if func_match:
        module = func_match.group(2)
        # Only return if module matches target or is a nested call we want to track
        if module == target_module:
            return {
                'type': 'function',
                'timestamp': parse_timestamp(func_match.group(1)),
                'timestamp_str': func_match.group(1),
                'module': module,
                'action': func_match.group(3),
                'function_name': func_match.group(4)
            }
    
    pref_match = re.match(pref_pattern, line)
    if pref_match:
        return {
            'type': 'pref_cd',
            'timestamp': parse_timestamp(pref_match.group(1)),
            'pref_cd': pref_match.group(2)
        }
    
    return None


def analyze_log(log_file: str, target_module: str) -> list[FunctionRecord]:
    """
    Analyze the log file and calculate execution times.
    Returns a list of FunctionRecord objects.
    """
    with open(log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Track current state
    current_pref_cd = "GLOBAL"  # For functions before any Pref Cd
    function_stack = {}  # Stack to track nested function calls: {func_name: [start_info, ...]}
    results: list[FunctionRecord] = []
    
    for line in lines:
        parsed = parse_log_line(line, target_module)
        if not parsed:
            continue
        
        if parsed['type'] == 'pref_cd':
            current_pref_cd = parsed['pref_cd']
        
        elif parsed['type'] == 'function':
            func_name = parsed['function_name']
            action = parsed['action']
            timestamp = parsed['timestamp']
            timestamp_str = parsed['timestamp_str']
            
            if action == 'Start':
                if func_name not in function_stack:
                    function_stack[func_name] = []
                function_stack[func_name].append({
                    'start': timestamp,
                    'start_str': timestamp_str,
                    'pref_cd': current_pref_cd
                })
            elif action == 'End':
                if func_name in function_stack and function_stack[func_name]:
                    start_info = function_stack[func_name].pop()
                    duration = (timestamp - start_info['start']).total_seconds()
                    
                    record = FunctionRecord(
                        pref_cd=start_info['pref_cd'],
                        function=func_name,
                        start_time=start_info['start_str'],
                        end_time=timestamp_str,
                        duration_sec=round(duration, 6)
                    )
                    results.append(record)
    
    return results


def export_to_csv(results: list[FunctionRecord], output_file: str):
    """Export results to CSV file."""
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['pref_cd', 'function', 'start_time', 'end_time', 'duration_sec'])
        
        for record in results:
            writer.writerow([
                record.pref_cd,
                record.function,
                record.start_time,
                record.end_time,
                record.duration_sec
            ])
    
    print(f"✅ Results exported to: {output_file}")
    print(f"   Total records: {len(results)}")


def print_usage():
    """Print usage information."""
    print("""
Usage:
    python log_analyzer.py <module_name> <input_log_file> <output_csv_file>

Arguments:
    module_name      - The module name to filter (e.g., FORM_LONG_TERM_CARE_FACILITY)
    input_log_file   - Path to the input log file
    output_csv_file  - Path to the output CSV file

Example:
    python log_analyzer.py FORM_LONG_TERM_CARE_FACILITY log result.csv
""")


if __name__ == "__main__":
    # Hardcoded configuration
    module_name = "FORM_LONG_TERM_CARE_FACILITY"
    input_file = "log"
    output_file = "result.csv"
    
    if not os.path.exists(input_file):
        print(f"❌ Error: Input log file not found: {input_file}")
        sys.exit(1)
    
    print(f"📊 Analyzing log file: {input_file}")
    print(f"   Target module: {module_name}")
    
    results = analyze_log(input_file, module_name)
    
    if not results:
        print(f"⚠️  Warning: No matching records found for module '{module_name}'")
    
    export_to_csv(results, output_file)
