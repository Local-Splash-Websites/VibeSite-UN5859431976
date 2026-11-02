<?php
// Receives the site's lead forms and forwards them to the leads API.
// Settings come from the environment or from a .env file one level above the web root.

declare(strict_types=1);

function env_value(string $key, string $default = ''): string {
    static $file = null;
    $v = getenv($key);
    if ($v !== false && $v !== '') return $v;
    if ($file === null) {
        $file = [];
        $path = dirname(__DIR__) . '/.env';
        if (is_readable($path)) {
            foreach (file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
                if ($line[0] === '#' || strpos($line, '=') === false) continue;
                [$k, $val] = explode('=', $line, 2);
                $file[trim($k)] = trim($val, " \t\"'");
            }
        }
    }
    return $file[$key] ?? $default;
}

function respond(int $code, array $body): void {
    $wantsJson = stripos($_SERVER['HTTP_ACCEPT'] ?? '', 'application/json') !== false;
    http_response_code($code);
    if ($wantsJson) {
        header('Content-Type: application/json');
        echo json_encode($body);
    } else {
        $back = '/contact-us';
        header('Location: ' . $back . ($body['ok'] ? '?sent=1' : '?error=1'), true, 303);
    }
    exit;
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    header('Allow: POST');
    respond(405, ['ok' => false, 'error' => 'Use the form to send a message.']);
}

// Honeypot: real visitors never see or fill this field. Pretend success for bots.
if (trim($_POST['website'] ?? '') !== '') {
    respond(200, ['ok' => true]);
}

$clean = function (string $key, int $max = 200): string {
    $v = trim((string)($_POST[$key] ?? ''));
    $v = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/u', '', $v) ?? '';
    return mb_substr($v, 0, $max);
};

$lead = [
    'name'    => $clean('name', 120),
    'phone'   => $clean('phone', 40),
    'email'   => $clean('email', 160),
    'service' => $clean('service', 80),
    'message' => $clean('message', 4000),
    'consent' => ($_POST['consent'] ?? '') === 'yes',
    'form_id' => $clean('form_id', 60),
];

if ($lead['name'] === '') respond(422, ['ok' => false, 'error' => 'Enter your name.']);
if (strlen(preg_replace('/\D/', '', $lead['phone'])) < 10) respond(422, ['ok' => false, 'error' => 'Enter a valid phone number, like +1 555-123-4567.']);
if (!filter_var($lead['email'], FILTER_VALIDATE_EMAIL)) respond(422, ['ok' => false, 'error' => 'Enter an email address with @ and a domain.']);
if (!$lead['consent']) respond(422, ['ok' => false, 'error' => 'Check the box to agree to the privacy policy before submitting.']);

$apiUrl = env_value('LEADS_API_URL');
$payload = $lead + [
    'site_name'    => env_value('LEADS_SITE_NAME', 'd8e4a61f'),
    'page'         => mb_substr((string)($_SERVER['HTTP_REFERER'] ?? ''), 0, 500),
    'ip'           => $_SERVER['REMOTE_ADDR'] ?? '',
    'user_agent'   => mb_substr((string)($_SERVER['HTTP_USER_AGENT'] ?? ''), 0, 300),
    'submitted_at' => gmdate('c'),
];

if ($apiUrl === '') {
    error_log('lead-webhook: LEADS_API_URL is not set; lead not forwarded: ' . json_encode($payload));
    respond(503, ['ok' => false, 'error' => "That didn't work. The form wasn't sent. Please call us instead."]);
}

$headers = ['Content-Type: application/json', 'Accept: application/json'];
$key = env_value('LEADS_API_KEY');
if ($key !== '') $headers[] = 'Authorization: Bearer ' . $key;

$ch = curl_init($apiUrl);
curl_setopt_array($ch, [
    CURLOPT_POST           => true,
    CURLOPT_POSTFIELDS     => json_encode($payload),
    CURLOPT_HTTPHEADER     => $headers,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT        => 15,
]);
$resp = curl_exec($ch);
$status = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
$err = curl_error($ch);
curl_close($ch);

if ($resp === false || $status < 200 || $status >= 300) {
    error_log("lead-webhook: leads API failed ($status) $err " . substr((string)$resp, 0, 500));
    respond(502, ['ok' => false, 'error' => "That didn't work. The form wasn't sent. Please try again or call us."]);
}

respond(200, ['ok' => true]);
