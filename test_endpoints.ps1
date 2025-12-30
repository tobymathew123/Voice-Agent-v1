# Test script for Voice Agent endpoints

Write-Host "Testing Voice Agent Endpoints..." -ForegroundColor Green

# Test 1: Health check
Write-Host "`n1. Testing health endpoint..." -ForegroundColor Cyan
$health = Invoke-WebRequest -Uri "http://localhost:8000/health/" -UseBasicParsing
Write-Host "Response: $($health.Content)" -ForegroundColor Yellow

# Test 2: Incoming call webhook
Write-Host "`n2. Testing incoming call webhook..." -ForegroundColor Cyan
$incomingCall = Invoke-WebRequest -Uri "http://localhost:8000/telephony/incoming" `
    -Method POST `
    -Body @{
        CallSid="CA987654321ABC"
        From="+15551234567"
        To="+15559876543"
        CallStatus="ringing"
    } `
    -UseBasicParsing

Write-Host "Response Content-Type: $($incomingCall.Headers.'Content-Type')" -ForegroundColor Yellow
Write-Host "XML Response:" -ForegroundColor Yellow
Write-Host $incomingCall.Content

# Test 3: Check active sessions
Write-Host "`n3. Checking active sessions..." -ForegroundColor Cyan
$sessions = Invoke-WebRequest -Uri "http://localhost:8000/telephony/sessions" -UseBasicParsing
Write-Host "Sessions: $($sessions.Content)" -ForegroundColor Yellow

# Test 4: Get specific session
Write-Host "`n4. Getting session details..." -ForegroundColor Cyan
$session = Invoke-WebRequest -Uri "http://localhost:8000/telephony/session/CA987654321ABC" -UseBasicParsing
Write-Host "Session Details:" -ForegroundColor Yellow
Write-Host $session.Content

# Test 5: Simulate gather response (user speech)
Write-Host "`n5. Testing gather response (simulated user speech)..." -ForegroundColor Cyan
$gatherResponse = Invoke-WebRequest -Uri "http://localhost:8000/telephony/gather/CA987654321ABC" `
    -Method POST `
    -Body @{
        CallSid="CA987654321ABC"
        SpeechResult="I need help with my account balance"
    } `
    -UseBasicParsing

Write-Host "XML Response:" -ForegroundColor Yellow
Write-Host $gatherResponse.Content

Write-Host "`nAll tests completed!" -ForegroundColor Green
