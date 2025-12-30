# Test script for outbound call endpoints

Write-Host "Testing Outbound Call Endpoints..." -ForegroundColor Green

# Test 1: Initiate notification call
Write-Host "`n1. Testing notification call initiation..." -ForegroundColor Cyan
$notificationCall = Invoke-WebRequest -Uri "http://localhost:8000/telephony/outbound/notification" `
    -Method POST `
    -Body (@{
        to_number="+15559876543"
        notification_type="otp"
        message="Your OTP is 123456. This code is valid for 5 minutes."
        priority="high"
        reference_id="OTP-2025-001"
    } | ConvertTo-Json) `
    -ContentType "application/json" `
    -UseBasicParsing

Write-Host "Response:" -ForegroundColor Yellow
Write-Host $notificationCall.Content

# Test 2: Initiate marketing call
Write-Host "`n2. Testing marketing call initiation..." -ForegroundColor Cyan
$marketingCall = Invoke-WebRequest -Uri "http://localhost:8000/telephony/outbound/marketing" `
    -Method POST `
    -Body (@{
        to_number="+15551234567"
        campaign_id="CAMP-2025-Q1-001"
        campaign_name="Premium Credit Card Offer"
        segment="high_value_customers"
        objective="product_promotion"
    } | ConvertTo-Json) `
    -ContentType "application/json" `
    -UseBasicParsing

Write-Host "Response:" -ForegroundColor Yellow
Write-Host $marketingCall.Content

# Test 3: Check active sessions
Write-Host "`n3. Checking active sessions..." -ForegroundColor Cyan
$sessions = Invoke-WebRequest -Uri "http://localhost:8000/telephony/sessions" -UseBasicParsing
Write-Host "Sessions:" -ForegroundColor Yellow
Write-Host $sessions.Content

Write-Host "`nAll tests completed!" -ForegroundColor Green
