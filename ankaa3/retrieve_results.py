"""Retrieve completed Ankaa-3 tasks and save their measurement results."""
from braket.aws import AwsDevice
from braket.aws.aws_quantum_task import AwsQuantumTask
import json
import os
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path(os.environ.get(
    "ANKAA3_OUTPUT_DIR",
    Path(__file__).resolve().parent / "outputs"
))

def retrieve_results(metadata_file):
    """Retrieve the tasks listed in a submission metadata file."""
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    print("="*60)
    print("RETRIEVING RIGETTI RESULTS")
    print("="*60)
    print(f"Experiment: {metadata['experiment']}")
    print(f"Submitted: {metadata['timestamp']}")
    print(f"Tasks: {len(metadata['tasks'])}")
    
    results = []
    
    for task_info in metadata['tasks']:
        task_id = task_info['task_id']
        hold_us = task_info['hold_us']
        
        print(f"\n{'='*60}")
        print(f"Retrieving: {hold_us:.1f} μs hold")
        
        try:
            task = AwsQuantumTask(arn=task_id)

            status = task.state()
            print(f"  Status: {status}")
            
            if status == "COMPLETED":
                result = task.result()
                measurements = result.measurements
                measurement_counts = result.measurement_counts
                
                bitstring_counts = {}
                for bitstring, count in measurement_counts.items():
                    bitstring_counts[bitstring] = int(count)
                
                total_shots = sum(bitstring_counts.values())
                
                print(f"  ✓ Retrieved {total_shots} shots")
                print(f"  Unique outcomes: {len(bitstring_counts)}")
                
                results.append({
                    "hold_ns": task_info['hold_ns'],
                    "hold_us": hold_us,
                    "status": "completed",
                    "total_shots": total_shots,
                    "measurement_counts": bitstring_counts,
                    "metadata": {
                        "execution_duration": result.task_metadata.executionDuration,
                        "shots": result.task_metadata.shots
                    }
                })
                
            elif status == "FAILED":
                print(f"  ✗ FAILED")
                results.append({
                    "hold_ns": task_info['hold_ns'],
                    "hold_us": hold_us,
                    "status": "failed",
                    "error": str(task.metadata())
                })
                
            else:
                print(f"  ⏳ Still running: {status}")
                results.append({
                    "hold_ns": task_info['hold_ns'],
                    "hold_us": hold_us,
                    "status": status.lower()
                })
                
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            results.append({
                "hold_ns": task_info['hold_ns'],
                "hold_us": hold_us,
                "status": "error",
                "error": str(e)
            })
    
    output = {
        "experiment": metadata['experiment'],
        "submission_time": metadata['timestamp'],
        "retrieval_time": datetime.now().isoformat(),
        "device": metadata['device'],
        "config": metadata['config'],
        "results": results
    }
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"rigetti_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"✓ Saved: {output_file}")
    
    completed = sum(1 for r in results if r['status'] == 'completed')
    failed = sum(1 for r in results if r['status'] == 'failed')
    running = sum(1 for r in results if r['status'] not in ['completed', 'failed', 'error'])
    
    print(f"\nSUMMARY:")
    print(f"  Completed: {completed}/{len(results)}")
    print(f"  Failed: {failed}/{len(results)}")
    print(f"  Running: {running}/{len(results)}")
    
    if completed == len(results):
        print(f"\n✓ ALL TASKS COMPLETE!")
        print(f"  Run the parity analysis script with {output_file}")
    elif running > 0:
        print(f"\n⏳ {running} tasks still running")
        print(f"  Wait 10-30 min and re-run this script")
    
    return output_file

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python retrieve_results.py <metadata_file.json>")
        print("\nExample:")
        print("  python retrieve_results.py rigetti_ghz_hold_time_20260119_143022.json")
        sys.exit(1)
    
    metadata_file = sys.argv[1]
    retrieve_results(metadata_file)
