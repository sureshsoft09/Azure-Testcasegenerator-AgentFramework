# azure-provision.ps1
# Provisions all Azure resources needed to host the three services.
# Run once before the first GitHub Actions deployment.
#
# NOTE: Resource Group and App Service Plan already exist – this script
#       skips their creation and reuses them.
#
# Prerequisites:
#   1. Azure CLI installed  (winget install Microsoft.AzureCLI)
#   2. Logged in           (az login)
#   3. Docker Desktop running (needed only if you want to push images manually)
#
# Usage:
#   .\deploy\azure-provision.ps1
# or override defaults:
#   .\deploy\azure-provision.ps1 -ResourceGroup "my-rg" -AppPlanName "my-plan"

param(
    [string]$ResourceGroup   = "rg-shared-bluebolt",          # existing resource group
    [string]$AcrName         = "testgenacr",                   # must be globally unique, lowercase
    [string]$AppPlanName     = "ASP-rgsharedbluebolt-919e",    # existing App Service Plan
    [string]$BackendAppName  = "testgen-backend",              # must be globally unique
    [string]$FrontendAppName = "testgen-frontend",             # must be globally unique
    [string]$JiraMcpAppName  = "testgen-jira-mcp"             # must be globally unique
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host ('`n=== Azure Test Generator - Resource Provisioning ===')
Write-Host ('Resource Group : ' + $ResourceGroup + '  (existing)')
Write-Host ('App Plan       : ' + $AppPlanName + '  (existing)')

# ── 1. Azure Container Registry ──────────────────────────────────────────────
Write-Host "`n[1/5] Creating Azure Container Registry '$AcrName'..."
az acr create `
    --resource-group $ResourceGroup `
    --name           $AcrName `
    --sku            Basic `
    --admin-enabled  true | Out-Null

$AcrLoginServer = az acr show --name $AcrName --query loginServer -o tsv
$AcrUser        = az acr credential show --name $AcrName --query username -o tsv
$AcrPass        = az acr credential show --name $AcrName --query "passwords[0].value" -o tsv
Write-Host ("      ACR login server : " + $AcrLoginServer)
Write-Host ("      ACR admin user   : " + $AcrUser)

# ── 2. Backend Web App ────────────────────────────────────────────────────────
Write-Host "`n[2/5] Creating Backend Web App '$BackendAppName'..."
az webapp create `
    --name            $BackendAppName `
    --resource-group  $ResourceGroup `
    --plan            $AppPlanName `
    --deployment-container-image-name "${AcrLoginServer}/testgen-backend:latest" | Out-Null

# Configure ACR admin credentials on the Web App (no role assignment needed)
az webapp config container set `
    --name                            $BackendAppName `
    --resource-group                  $ResourceGroup `
    --docker-registry-server-url      "https://${AcrLoginServer}" `
    --docker-registry-server-user     $AcrUser `
    --docker-registry-server-password $AcrPass `
    --docker-custom-image-name        "${AcrLoginServer}/testgen-backend:latest" | Out-Null

$BackendCdUrl = az webapp deployment container config `
    --enable-cd true --name $BackendAppName --resource-group $ResourceGroup `
    --query CI_CD_URL -o tsv

az webapp config appsettings set `
    --name           $BackendAppName `
    --resource-group $ResourceGroup `
    --settings `
        WEBSITES_PORT=8000 `
        APP_ENV=production `
        CORS_ORIGINS="[`"https://${FrontendAppName}.azurewebsites.net`"]" | Out-Null

# ── 3. Jira MCP Web App ───────────────────────────────────────────────────────
Write-Host "`n[3/5] Creating Jira MCP Web App '$JiraMcpAppName'..."
az webapp create `
    --name            $JiraMcpAppName `
    --resource-group  $ResourceGroup `
    --plan            $AppPlanName `
    --deployment-container-image-name "${AcrLoginServer}/testgen-jira-mcp:latest" | Out-Null

az webapp config container set `
    --name                            $JiraMcpAppName `
    --resource-group                  $ResourceGroup `
    --docker-registry-server-url      "https://${AcrLoginServer}" `
    --docker-registry-server-user     $AcrUser `
    --docker-registry-server-password $AcrPass `
    --docker-custom-image-name        "${AcrLoginServer}/testgen-jira-mcp:latest" | Out-Null

$JiraCdUrl = az webapp deployment container config `
    --enable-cd true --name $JiraMcpAppName --resource-group $ResourceGroup `
    --query CI_CD_URL -o tsv

az webapp config appsettings set `
    --name           $JiraMcpAppName `
    --resource-group $ResourceGroup `
    --settings `
        WEBSITES_PORT=8002 `
        MCP_HOST=0.0.0.0 `
        MCP_PORT=8002 `
        MCP_TRANSPORT=http | Out-Null

# ── 4. Frontend Web App ───────────────────────────────────────────────────────
Write-Host "`n[4/5] Creating Frontend Web App '$FrontendAppName'..."
az webapp create `
    --name            $FrontendAppName `
    --resource-group  $ResourceGroup `
    --plan            $AppPlanName `
    --deployment-container-image-name "${AcrLoginServer}/testgen-frontend:latest" | Out-Null

az webapp config container set `
    --name                            $FrontendAppName `
    --resource-group                  $ResourceGroup `
    --docker-registry-server-url      "https://${AcrLoginServer}" `
    --docker-registry-server-user     $AcrUser `
    --docker-registry-server-password $AcrPass `
    --docker-custom-image-name        "${AcrLoginServer}/testgen-frontend:latest" | Out-Null

$FrontendCdUrl = az webapp deployment container config `
    --enable-cd true --name $FrontendAppName --resource-group $ResourceGroup `
    --query CI_CD_URL -o tsv

az webapp config appsettings set `
    --name           $FrontendAppName `
    --resource-group $ResourceGroup `
    --settings `
        BACKEND_URL="https://${BackendAppName}.azurewebsites.net" | Out-Null

Write-Host ("`n=== Provisioning complete! ===")
Write-Host ""
Write-Host "Add these 6 secrets to your GitHub repository"
Write-Host "(Settings -> Secrets and variables -> Actions):"
Write-Host ""
Write-Host ("  ACR_LOGIN_SERVER    " + $AcrLoginServer)
Write-Host ("  ACR_USERNAME        " + $AcrUser)
Write-Host ("  ACR_PASSWORD        " + $AcrPass)
Write-Host ("  BACKEND_CD_URL      " + $BackendCdUrl)
Write-Host ("  JIRA_MCP_CD_URL     " + $JiraCdUrl)
Write-Host ("  FRONTEND_CD_URL     " + $FrontendCdUrl)
Write-Host ""
Write-Host "NOTE: No Azure service principal needed."
Write-Host "      GitHub Actions pushes images to ACR, then POSTs to each CD URL to trigger restart."
Write-Host ""
Write-Host "After provisioning, set sensitive app settings (run manually):"
Write-Host ("  az webapp config appsettings set --name " + $BackendAppName + " --resource-group " + $ResourceGroup + " --settings COSMOS_DB_URL=<url> COSMOS_DB_KEY=<key> AZURE_OPENAI_ENDPOINT=<ep> AZURE_OPENAI_API_KEY=<key> AZURE_STORAGE_CONNECTION_STRING=<conn>")
Write-Host ("  az webapp config appsettings set --name " + $JiraMcpAppName + " --resource-group " + $ResourceGroup + " --settings JIRA_URL=<url> JIRA_EMAIL=<email> JIRA_API_TOKEN=<token>")
