@echo off
REM Script Windows pour pousser le schéma SQL vers Supabase via psql
REM Usage: scripts\push_schema_psql.bat

setlocal

REM Charger les variables d'environnement depuis .env
if exist backend\.env (
    for /f "tokens=*" %%a in (backend\.env) do (
        set "%%a"
    )
)

if "%DB_HOST%"=="" (
    echo ❌ Erreur: Variable DB_HOST non définie
    exit /b 1
)
if "%DB_NAME%"=="" (
    echo ❌ Erreur: Variable DB_NAME non définie
    exit /b 1
)
if "%DB_USER%"=="" (
    echo ❌ Erreur: Variable DB_USER non définie
    exit /b 1
)
if "%DB_PASSWORD%"=="" (
    echo ❌ Erreur: Variable DB_PASSWORD non définie
    exit /b 1
)

set SCHEMA_FILE=supabase\schema.sql

if not exist "%SCHEMA_FILE%" (
    echo ❌ Erreur: Fichier %SCHEMA_FILE% introuvable
    exit /b 1
)

echo 📤 Connexion à Supabase...
echo    Host: %DB_HOST%
echo    Database: %DB_NAME%
echo    User: %DB_USER%

REM Construire la connection string
set CONNECTION_STRING=postgresql://%DB_USER%:%DB_PASSWORD%@%DB_HOST%:%DB_PORT%/%DB_NAME%

echo 📝 Exécution du schéma SQL...
psql "%CONNECTION_STRING%" -f "%SCHEMA_FILE%"

if %ERRORLEVEL% EQU 0 (
    echo ✅ Schéma appliqué avec succès!
) else (
    echo ❌ Erreur lors de l'exécution
    exit /b 1
)

endlocal

