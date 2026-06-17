#!/usr/bin/env python3
"""
Pull and analyze training metrics from CloudWatch.

Usage:
    python pull_training_metrics.py xgbregressor-training-20260617120000
"""

import argparse
import boto3
import json
from datetime import datetime, timedelta
from typing import List, Dict


def get_training_logs(job_name: str, log_type: str = "stdout") -> List[str]:
    """Get training logs from CloudWatch."""
    logs_client = boto3.client('logs')

    log_group = '/aws/sagemaker/TrainingJobs'
    log_stream = f'{job_name}/algo-1-{log_type}'

    print(f"Fetching logs from {log_stream}...")

    try:
        response = logs_client.get_log_events(
            logGroupName=log_group,
            logStreamName=log_stream,
            startFromHead=True
        )
        return [event['message'] for event in response['events']]
    except Exception as e:
        print(f"Error fetching logs: {e}")
        return []


def extract_metrics(logs: List[str]) -> List[Dict]:
    """Extract metrics from log lines."""
    metrics = []

    for line in logs:
        if '[METRICS]' in line:
            metrics.append(line.strip())

    return metrics


def print_metrics_summary(metrics: List[str]):
    """Print a summary of metrics."""
    if not metrics:
        print("No metrics found in logs")
        return

    print(f"\n{'='*80}")
    print(f"METRICS SUMMARY ({len(metrics)} samples)")
    print(f"{'='*80}\n")

    # Parse metrics
    cpu_values = []
    memory_values = []
    gpu_values = []

    for line in metrics:
        # Parse CPU
        if 'CPU:' in line:
            try:
                cpu_str = line.split('CPU:')[1].split('%')[0].strip()
                cpu_values.append(float(cpu_str))
            except:
                pass

        # Parse Memory
        if 'Memory:' in line:
            try:
                mem_str = line.split('Memory:')[1].split('%')[0].strip()
                # Extract percentage at the end
                mem_percent = float(mem_str.split()[-1].strip('()'))
                memory_values.append(mem_percent)
            except:
                pass

    # Print summary
    if cpu_values:
        print(f"CPU Utilization:")
        print(f"  Min:  {min(cpu_values):6.1f}%")
        print(f"  Max:  {max(cpu_values):6.1f}%")
        print(f"  Avg:  {sum(cpu_values)/len(cpu_values):6.1f}%")

    if memory_values:
        print(f"\nMemory Utilization:")
        print(f"  Min:  {min(memory_values):6.1f}%")
        print(f"  Max:  {max(memory_values):6.1f}%")
        print(f"  Avg:  {sum(memory_values)/len(memory_values):6.1f}%")

    print(f"\n{'='*80}")
    print("METRICS TIMELINE")
    print(f"{'='*80}\n")

    # Print full metrics
    for i, metric in enumerate(metrics, 1):
        print(f"{i:3d}. {metric}")


def get_training_job_info(job_name: str):
    """Get training job details from SageMaker."""
    sm_client = boto3.client('sagemaker')

    try:
        response = sm_client.describe_training_job(TrainingJobName=job_name)

        print(f"\n{'='*80}")
        print("TRAINING JOB DETAILS")
        print(f"{'='*80}")
        print(f"Job Name:       {response['TrainingJobName']}")
        print(f"Status:         {response['TrainingJobStatus']}")
        print(f"Instance Type:  {response['ResourceConfig']['InstanceType']}")
        print(f"Instance Count: {response['ResourceConfig']['InstanceCount']}")

        # Calculate duration
        if 'TrainingEndTime' in response:
            start = response['CreationTime']
            end = response['TrainingEndTime']
            duration = (end - start).total_seconds() / 60
            print(f"Duration:       {duration:.1f} minutes")

        print(f"{'='*80}\n")

    except Exception as e:
        print(f"Error fetching job details: {e}")


def main():
    parser = argparse.ArgumentParser(description="Pull training metrics from CloudWatch")
    parser.add_argument("job_name", help="SageMaker training job name")
    parser.add_argument("--log-type", default="stdout", choices=["stdout", "stderr"],
                        help="Which log stream to fetch (default: stdout)")
    parser.add_argument("--save-json", help="Save metrics to JSON file")
    args = parser.parse_args()

    # Get job info
    get_training_job_info(args.job_name)

    # Get logs
    logs = get_training_logs(args.job_name, args.log_type)

    if not logs:
        print("No logs found")
        return

    # Extract and display metrics
    metrics = extract_metrics(logs)
    print_metrics_summary(metrics)

    # Save to JSON if requested
    if args.save_json:
        with open(args.save_json, 'w') as f:
            json.dump({
                'job_name': args.job_name,
                'log_type': args.log_type,
                'metrics': metrics,
                'extracted_at': datetime.now().isoformat()
            }, f, indent=2)
        print(f"Metrics saved to {args.save_json}")


if __name__ == "__main__":
    main()
