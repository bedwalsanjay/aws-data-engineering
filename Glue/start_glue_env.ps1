# ── Start Glue + MinIO local development environment ──────────────────────────

# Step 1: Start Glue container in detached mode
Write-Host "`n[1/5] Starting Glue container..." -ForegroundColor Cyan

docker run -d `
    --entrypoint /home/glue_user/.local/bin/jupyter `
    -v "$env:USERPROFILE\.aws:/home/glue_user/.aws" `
    -v "$env:USERPROFILE\Desktop\repos\de_projects\aws-data-engineering\Glue\notebooks:/home/glue_user/workspace" `
    -e AWS_PROFILE=default `
    -e DISABLE_SSL=true `
    --rm `
    -p 4040:4040 `
    -p 18080:18080 `
    -p 8888:8888 `
    --name glue_container `
    amazon/aws-glue-libs:glue_libs_4.0.0_image_01 `
    notebook --ip=0.0.0.0 --port=8888 --allow-root --NotebookApp.token=''

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to start Glue container. Is it already running?" -ForegroundColor Red
    exit 1
}

# Wait for Glue container to be ready
Write-Host "Waiting for Glue container to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Start Spark History Server
Write-Host "Starting Spark History Server..." -ForegroundColor Cyan
docker exec glue_container bash -c '$SPARK_HOME/sbin/start-history-server.sh'

# Step 2: Create Docker network (ignore if already exists)
Write-Host "`n[2/5] Creating Docker network 'glue-minio-network'..." -ForegroundColor Cyan

docker network create glue-minio-network 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Network created." -ForegroundColor Green
} else {
    Write-Host "Network already exists, skipping." -ForegroundColor Yellow
}

# Step 3: Start MinIO container
Write-Host "`n[3/5] Starting MinIO container..." -ForegroundColor Cyan

docker run -d `
    --name minio `
    --network glue-minio-network `
    -p 9000:9000 `
    -p 9001:9001 `
    -e MINIO_ROOT_USER=minioadmin `
    -e MINIO_ROOT_PASSWORD=minioadmin `
    -v "$env:USERPROFILE\minio-data:/data" `
    minio/minio server /data --console-address ":9001"

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to start MinIO container. Is it already running?" -ForegroundColor Red
    exit 1
}

# Step 4: Connect Glue container to MinIO network
Write-Host "`n[4/5] Connecting Glue container to glue-minio-network..." -ForegroundColor Cyan

docker network connect glue-minio-network glue_container

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to connect glue_container to network." -ForegroundColor Red
    exit 1
}

# Step 5: Print URLs
Write-Host "`n[5/5] All services are up!" -ForegroundColor Green
Write-Host "─────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host "  Jupyter Notebook   : http://localhost:8888" -ForegroundColor White
Write-Host "  Spark UI           : http://localhost:4040" -ForegroundColor White
Write-Host "  Spark History      : http://localhost:18080" -ForegroundColor White
Write-Host "  MinIO Console      : http://localhost:9001" -ForegroundColor White
Write-Host "    Username         : minioadmin" -ForegroundColor White
Write-Host "    Password         : minioadmin" -ForegroundColor White
Write-Host "  MinIO API          : http://localhost:9000" -ForegroundColor White
Write-Host "─────────────────────────────────────────────" -ForegroundColor DarkGray
