Write-Host ""
Write-Host "=========== DIAGNOSTICO ===========" -ForegroundColor Cyan

docker ps

Write-Host ""
Write-Host "=========== HEALTH RASA ===========" -ForegroundColor Cyan

docker exec rasa sh -lc "curl -s http://localhost:5005/status"

Write-Host ""
Write-Host "=========== HEALTH ACTION ===========" -ForegroundColor Cyan

docker exec action-server sh -lc "curl -s http://localhost:5055/health"

Write-Host ""
Write-Host "=========== HEALTH OLLAMA ===========" -ForegroundColor Cyan

docker exec ollama sh -lc "curl -s http://localhost:11434/api/tags"

Write-Host ""
Write-Host "=========== HEALTH BACKEND ===========" -ForegroundColor Cyan

docker exec backend sh -lc "curl -s http://localhost:8000/api/health"

Write-Host ""
Write-Host "=========== HEALTH MONGO ===========" -ForegroundColor Cyan

docker exec mongo mongosh --quiet --eval "db.adminCommand('ping')"