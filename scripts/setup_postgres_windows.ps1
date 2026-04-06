<#
.SYNOPSIS
PostgreSQL 1-Click Installation and Setup for Windows

.DESCRIPTION
This script automates the process of setting up a local PostgreSQL database cluster
for the RAG Game QA System without requiring Administrator privileges.
It will:
1. Download the Postgres binaries
2. Extract to .postgres folder
3. Initialize the database (initdb)
4. Start the database (pg_ctl)
5. Create the required 'rag_game_qa' database and user

.NOTES
Run this script from the root of the project.
#>

$ErrorActionPreference = "Stop"

$PG_VERSION = "16.2-1" 
$PG_URL = "https://get.enterprisedb.com/postgresql/postgresql-$PG_VERSION-windows-x64-binaries.zip"
$ROOT_DIR = $PSScriptRoot | Split-Path -Parent
$PG_DIR = Join-Path $ROOT_DIR ".postgres"
$PG_BIN = Join-Path $PG_DIR "pgsql\bin"
$PG_DATA = Join-Path $PG_DIR "data"
$ZIP_FILE = Join-Path $ROOT_DIR "postgres-binaries.zip"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " PostgeSQL Windows 1-Click Setup started " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# 1. Download Postgres Binaries
if (-not (Test-Path $PG_BIN)) {
    Write-Host "[1/5] Downloading PostgreSQL $PG_VERSION binaries..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $PG_URL -OutFile $ZIP_FILE
    
    Write-Host "[2/5] Extracting archive..." -ForegroundColor Yellow
    Expand-Archive -Path $ZIP_FILE -DestinationPath $PG_DIR -Force
    Remove-Item -Path $ZIP_FILE -Force
} else {
    Write-Host "[1-2/5] PostgreSQL binaries already exist in $($PG_DIR)." -ForegroundColor Green
}

# 2. Init Cluster
if (-not (Test-Path $PG_DATA)) {
    Write-Host "[3/5] Initializing Database cluster..." -ForegroundColor Yellow
    $initdb = Join-Path $PG_BIN "initdb.exe"
    & $initdb -D $PG_DATA -U postgres -E UTF8 --locale=C
} else {
    Write-Host "[3/5] Database cluster already initialized." -ForegroundColor Green
}

# 3. Start Database
Write-Host "[4/5] Starting PostgreSQL..." -ForegroundColor Yellow
$pg_ctl = Join-Path $PG_BIN "pg_ctl.exe"

# 检查是否已经在运行
$status = & $pg_ctl status -D $PG_DATA 2>&1
if ($status -match "server is running") {
    Write-Host "[4/5] PostgreSQL is already running." -ForegroundColor Green
} else {
    & $pg_ctl start -D $PG_DATA -l $(Join-Path $PG_DIR "logfile.log") -w
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to start PostgreSQL."
        exit 1
    }
}

# 4. Create Database and User
Write-Host "[5/5] Configuring specific role and database..." -ForegroundColor Yellow
$psql = Join-Path $PG_BIN "psql.exe"

$setupSql = @"
DO `$body` BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'user') THEN
    CREATE ROLE "user" LOGIN PASSWORD 'password';
  END IF;
END `$body`;
CREATE DATABASE rag_game_qa OWNER "user";
"@

# Execute setup snippet
try {
    $setupSql | & $psql -U postgres -d postgres -v ON_ERROR_STOP=1 -q >$null 2>&1
    Write-Host "Database 'rag_game_qa' configured successfully!" -ForegroundColor Green
} catch {
    Write-Host "Database might already exist or error occurred. It's safe to continue." -ForegroundColor DarkYellow
}

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " Setup Complete! " -ForegroundColor Green
Write-Host " PostgreSQL is running at localhost:5432 " -ForegroundColor Cyan
Write-Host " Connection String: postgresql://user:password@localhost:5432/rag_game_qa" -ForegroundColor Cyan
Write-Host " Note: If you want to stop the server later, run: " -ForegroundColor Gray
Write-Host "  > .postgres\pgsql\bin\pg_ctl.exe stop -D .postgres\data" -ForegroundColor Gray
Write-Host "=========================================" -ForegroundColor Cyan
