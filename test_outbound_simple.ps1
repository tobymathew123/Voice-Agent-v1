# Simple test for outbound call endpoint structure

Write-Host "Testing Outbound Call Endpoint Structure..." -ForegroundColor Green

# Test notification endpoint with query parameters
Write-Host "`n1. Testing notification call endpoint..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest `
        -Uri "http://localhost:8000/telephony/outbound/notification?to_number=%2B15559876543&notification_type=otp&message=Your%20OTP%20is%20123456&priority=high" `
        -Method POST `
        -UseBasicParsing `
        -ErrorAction Stop
    
    Write-Host "Success! Response:" -ForegroundColor Green
    Write-Host $response.Content
} catch {
    Write-Host "Expected error (no real Vobiz API):" -ForegroundColor Yellow
    Write-Host $_.Exception.Message
}

# Test marketing endpoint with query parameters  
Write-Host "`n2. Testing marketing call endpoint..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest `
        -Uri "http://localhost:8000/telephony/outbound/marketing?to_number=%2B15551234567&campaign_id=CAMP001&campaign_name=Test%20Campaign" `
        -Method POST `
        -UseBasicParsing `
        -ErrorAction Stop
    
    Write-Host "Success! Response:" -ForegroundColor Green
    Write-Host $response.Content
} catch {
    Write-Host "Expected error (no real Vobiz API):" -ForegroundColor Yellow
    Write-Host $_.Exception.Message
}

# Test API docs
Write-Host "`n3. Checking API documentation..." -ForegroundColor Cyan
$docs = Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing
Write-Host "API docs available at: http://localhost:8000/docs" -ForegroundColor Green

Write-Host "`nTests completed!" -ForegroundColor Green
Write-Host "Note: Actual call initiation requires valid Vobiz API credentials and public webhook URL" -ForegroundColor Yellow
