$headers = @{
    "Authorization" = "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"
    "Content-Type"  = "application/json"
}

$body = @{
    model = "google/gemini-2.0-flash-001" # Or any model you have access to
    messages = @(
        @{ role = "user"; content = "Say 'Connection Successful'!" }
    )
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "https://openrouter.ai/api/v1/chat/completions" -Method Post -Headers $headers -Body $body
$response.choices[0].message.content