<?php
// Temporary: checks whether this container can reach the lead service. Sends no lead.
header('Content-Type: text/plain');
$u = (string)getenv('LEADS_SERVICE_URL');
echo 'env set: ' . ($u !== '' ? 'yes' : 'no') . "\n";
$h = parse_url($u, PHP_URL_HOST) ?: '';
echo 'host resolves: ' . ($h !== '' && gethostbyname($h) !== $h ? 'yes' : 'no') . "\n";
foreach (['/', '/healthz', '/health', '/v1/lead'] as $p) {
    $ch = curl_init(rtrim($u, '/') . $p);
    curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 8, CURLOPT_HTTPGET => true]);
    $r = curl_exec($ch);
    echo "GET $p -> " . (int)curl_getinfo($ch, CURLINFO_HTTP_CODE) . ' ' . curl_error($ch) . ' ' . substr(preg_replace('/\s+/', ' ', (string)$r), 0, 200) . "\n";
    curl_close($ch);
}
