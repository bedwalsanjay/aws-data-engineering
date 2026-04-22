import boto3
import time
import sys

def run_glue_job(job_name):
    glue = boto3.client('glue', region_name='ap-south-1')

    # ── Start the Glue job ────────────────────────────────────
    print(f"Starting Glue job: {job_name}")
    response = glue.start_job_run(JobName=job_name)
    job_run_id = response['JobRunId']
    print(f"Job Run ID: {job_run_id}")

    # ── Poll until job finishes ───────────────────────────────
    terminal_states = ['SUCCEEDED', 'FAILED', 'ERROR', 'STOPPED']

    while True:
        status_response = glue.get_job_run(
            JobName=job_name,
            RunId=job_run_id
        )
        status = status_response['JobRun']['JobRunState']
        print(f"Current status: {status}")

        if status in terminal_states:
            break

        print("Waiting 5 seconds...")
        time.sleep(5)

    # ── Print final result ────────────────────────────────────
    if status == 'SUCCEEDED':
        print(f"Job {job_name} completed successfully")
    else:
        error_message = status_response['JobRun'].get('ErrorMessage', 'No error message')
        print(f"Job {job_name} failed with status: {status}")
        print(f"Error: {error_message}")

    return status


# ── Run the script ────────────────────────────────────────────
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python glue_runner.py <job-name>")
        sys.exit(1)

    job_name = sys.argv[1]
    run_glue_job(job_name)
    