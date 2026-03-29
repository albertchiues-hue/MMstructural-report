<?php
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');

const TRANSLATE_API_URL = 'http://xrayai2.pohai.org.tw:9000/translate';
const LOCAL_LLM_API_URL = 'http://xrayai2.pohai.org.tw:8001/v1/chat/completions';

function respond(int $status, array $payload): void
{
    http_response_code($status);
    echo json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function sanitize_filename(string $value): string
{
    return preg_replace('/[\\\\\\/:*?"<>|]+/', '', trim($value)) ?? '';
}

function sanitize_subdir(string $value): string
{
    $value = str_replace('\\', '/', trim($value));
    $value = trim($value, '/');
    if ($value === '') {
        return '';
    }

    $segments = array_filter(
        explode('/', $value),
        static function ($segment) {
            return $segment !== '' && $segment !== '.' && $segment !== '..';
        }
    );

    return implode(DIRECTORY_SEPARATOR, $segments);
}

function sanitize_examname(string $value): string
{
    $sanitized = preg_replace('/[^a-z0-9_-]+/i', '', strtolower(trim($value))) ?? '';
    return $sanitized !== '' ? $sanitized : 'ldct';
}

function build_state_filename(string $patientId, string $examDate, string $examName): string
{
    return sanitize_filename($patientId) . '_' . sanitize_filename($examDate) . '-' . strtoupper(sanitize_examname($examName)) . '.json';
}

function build_state_filename_v2(string $accessionNumber, string $patientId): string
{
    return sanitize_filename($accessionNumber) . '_' . sanitize_filename($patientId) . '.json';
}

function build_available_path(string $directory, string $filename): string
{
    $pathInfo = pathinfo($filename);
    $targetPath = $directory . DIRECTORY_SEPARATOR . $filename;
    $counter = 2;
    while (file_exists($targetPath)) {
        $targetPath = $directory . DIRECTORY_SEPARATOR . $pathInfo['filename'] . '_v' . $counter . '.' . $pathInfo['extension'];
        $counter += 1;
    }
    return $targetPath;
}

function path_to_relative_url(string $path, string $root): string
{
    $relativePath = substr($path, strlen($root) + 1);
    return str_replace(DIRECTORY_SEPARATOR, '/', $relativePath);
}

function ends_with(string $haystack, string $needle): bool
{
    if ($needle === '') {
        return true;
    }

    $needleLength = strlen($needle);
    if ($needleLength > strlen($haystack)) {
        return false;
    }

    return substr($haystack, -$needleLength) === $needle;
}

function translate_via_api(array $payload): array
{
    $json = json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    if ($json === false) {
        respond(500, ['ok' => false, 'error' => 'Failed to encode translate payload.']);
    }

    if (function_exists('curl_init')) {
        $ch = curl_init(TRANSLATE_API_URL);
        curl_setopt_array($ch, [
            CURLOPT_POST => true,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
            CURLOPT_POSTFIELDS => $json,
            CURLOPT_CONNECTTIMEOUT => 5,
            CURLOPT_TIMEOUT => 20,
        ]);
        $response = curl_exec($ch);
        if ($response === false) {
            $error = curl_error($ch);
            curl_close($ch);
            respond(502, ['ok' => false, 'error' => 'Translate API request failed: ' . $error]);
        }
        $status = (int)curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
        curl_close($ch);
    } else {
        $context = stream_context_create([
            'http' => [
                'method' => 'POST',
                'header' => "Content-Type: application/json\r\n",
                'content' => $json,
                'timeout' => 20,
                'ignore_errors' => true,
            ],
        ]);
        $response = @file_get_contents(TRANSLATE_API_URL, false, $context);
        if ($response === false) {
            respond(502, ['ok' => false, 'error' => 'Translate API request failed.']);
        }
        $status = 200;
        if (isset($http_response_header[0]) && preg_match('/\s(\d{3})\s/', $http_response_header[0], $matches)) {
            $status = (int)$matches[1];
        }
    }

    $decoded = json_decode($response, true);
    if (!is_array($decoded)) {
        respond(502, ['ok' => false, 'error' => 'Translate API returned invalid JSON.', 'raw_response' => $response]);
    }

    if ($status < 200 || $status >= 300) {
        respond($status, ['ok' => false, 'error' => $decoded['error'] ?? 'Translate API returned an error.']);
    }

    return $decoded;
}

function call_local_llm_api(string $prompt): array
{
    $json = json_encode([
        'model' => 'local-model',
        'messages' => [['role' => 'user', 'content' => $prompt]],
        'temperature' => 0.2,
        'max_tokens' => 5120,
    ], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

    if ($json === false) {
        respond(500, ['ok' => false, 'error' => 'Failed to encode local LLM payload.']);
    }

    if (function_exists('curl_init')) {
        $ch = curl_init(LOCAL_LLM_API_URL);
        curl_setopt_array($ch, [
            CURLOPT_POST => true,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
            CURLOPT_POSTFIELDS => $json,
            CURLOPT_CONNECTTIMEOUT => 5,
            CURLOPT_TIMEOUT => 60,
        ]);
        $response = curl_exec($ch);
        if ($response === false) {
            $error = curl_error($ch);
            curl_close($ch);
            respond(502, ['ok' => false, 'error' => 'Local LLM request failed: ' . $error]);
        }
        $status = (int)curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
        curl_close($ch);
    } else {
        $context = stream_context_create([
            'http' => [
                'method' => 'POST',
                'header' => "Content-Type: application/json\r\n",
                'content' => $json,
                'timeout' => 60,
                'ignore_errors' => true,
            ],
        ]);
        $response = @file_get_contents(LOCAL_LLM_API_URL, false, $context);
        if ($response === false) {
            respond(502, ['ok' => false, 'error' => 'Local LLM request failed.']);
        }
        $status = 200;
        if (isset($http_response_header[0]) && preg_match('/\s(\d{3})\s/', $http_response_header[0], $matches)) {
            $status = (int)$matches[1];
        }
    }

    $decoded = json_decode($response, true);
    if (!is_array($decoded)) {
        respond(502, ['ok' => false, 'error' => 'Local LLM returned invalid JSON.', 'raw_response' => $response]);
    }

    if ($status < 200 || $status >= 300) {
        respond($status, ['ok' => false, 'error' => $decoded['error']['message'] ?? $decoded['error'] ?? 'Local LLM returned an error.']);
    }

    return $decoded;
}

$baseDir = __DIR__;

if ($_SERVER['REQUEST_METHOD'] === 'GET' && (string)($_GET['action'] ?? '') === 'load') {
    $subdir = sanitize_subdir((string)($_GET['output_subdir'] ?? ''));
    $examName = sanitize_examname((string)($_GET['examname'] ?? 'ldct'));
    $accessionNumber = (string)($_GET['accession_number'] ?? '');
    $patientId = (string)($_GET['patient_id'] ?? '');
    $examDate = (string)($_GET['exam_date'] ?? '');
    $rootDir = $baseDir . DIRECTORY_SEPARATOR . $examName . '_json';
    $targetDir = $subdir === '' ? $rootDir : $rootDir . DIRECTORY_SEPARATOR . $subdir;
    $stateFilename = $accessionNumber !== ''
        ? build_state_filename_v2($accessionNumber, $patientId)
        : build_state_filename($patientId, $examDate, $examName);
    $statePath = $targetDir . DIRECTORY_SEPARATOR . $stateFilename;

    if (!is_file($statePath)) {
        respond(404, ['ok' => false, 'error' => 'State file not found.']);
    }

    $raw = @file_get_contents($statePath);
    if ($raw === false) {
        respond(500, ['ok' => false, 'error' => 'Failed to read state file.']);
    }

    $state = json_decode($raw, true);
    if (!is_array($state)) {
        respond(500, ['ok' => false, 'error' => 'State file is invalid JSON.']);
    }

    respond(200, [
        'ok' => true,
        'state_path' => $statePath,
        'state' => $state,
    ]);
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    respond(405, ['ok' => false, 'error' => 'Method not allowed.']);
}

$rawBody = file_get_contents('php://input');
if ($rawBody === false || $rawBody === '') {
    respond(400, ['ok' => false, 'error' => 'Request body is empty.']);
}

$payload = json_decode($rawBody, true);
if (!is_array($payload)) {
    respond(400, ['ok' => false, 'error' => 'Invalid JSON body.']);
}

if ((string)($_GET['action'] ?? '') === 'translate') {
    $text = trim((string)($payload['text'] ?? ''));
    if ($text === '') {
        respond(400, ['ok' => false, 'error' => 'text is required.']);
    }

    $translated = translate_via_api([
        'text' => $text,
    ]);

    respond(200, [
        'ok' => true,
        'translated_text' => $translated['translated_text'] ?? $text,
        'model' => $translated['model'] ?? '',
    ]);
}

if ((string)($_GET['action'] ?? '') === 'local_llm') {
    $prompt = trim((string)($payload['prompt'] ?? ''));

    if ($prompt === '') {
        respond(400, ['ok' => false, 'error' => 'prompt is required.']);
    }

    $decoded = call_local_llm_api($prompt);
    $content = trim((string)($decoded['choices'][0]['message']['content'] ?? ''));

    if ($content === '') {
        respond(502, ['ok' => false, 'error' => 'Local LLM returned empty content.']);
    }

    respond(200, [
        'ok' => true,
        'content' => $content,
        'model' => (string)($decoded['model'] ?? ''),
        'endpoint' => LOCAL_LLM_API_URL,
    ]);
}

$stateFilename = sanitize_filename((string)($payload['state_filename'] ?? ''));
$subdir = sanitize_subdir((string)($payload['output_subdir'] ?? ''));
$examName = sanitize_examname((string)($payload['examname'] ?? 'ldct'));
$statePayload = $payload['state'] ?? null;

if ($stateFilename === '' || !ends_with(strtolower($stateFilename), '.json')) {
    respond(400, ['ok' => false, 'error' => 'A valid .json state filename is required.']);
}

if (!is_array($statePayload)) {
    respond(400, ['ok' => false, 'error' => 'state is required.']);
}
$jsonRootDir = $baseDir . DIRECTORY_SEPARATOR . $examName . '_json';
$jsonTargetDir = $subdir === '' ? $jsonRootDir : $jsonRootDir . DIRECTORY_SEPARATOR . $subdir;

if (!is_dir($jsonTargetDir) && !@mkdir($jsonTargetDir, 0775, true) && !is_dir($jsonTargetDir)) {
    respond(500, ['ok' => false, 'error' => 'Failed to create JSON target directory.']);
}

$statePath = $jsonTargetDir . DIRECTORY_SEPARATOR . $stateFilename;
$stateJson = json_encode($statePayload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT);
if ($stateJson === false) {
    respond(500, ['ok' => false, 'error' => 'Failed to encode state JSON.']);
}

if (@file_put_contents($statePath, $stateJson) === false) {
    respond(500, [
        'ok' => false,
        'error' => 'Failed to save state file.',
        'state_path' => $statePath,
        'json_target_dir' => $jsonTargetDir,
        'json_target_dir_exists' => is_dir($jsonTargetDir),
        'json_target_dir_writable' => is_writable($jsonTargetDir),
    ]);
}

if ((string)($_GET['action'] ?? '') === 'save_state') {
    respond(200, [
        'ok' => true,
        'state_path' => $statePath,
    ]);
}

$filename = sanitize_filename((string)($payload['filename'] ?? ''));
$isPdf = ends_with(strtolower($filename), '.pdf');
$isDocx = ends_with(strtolower($filename), '.docx');

if ($filename === '' || (!$isDocx && !$isPdf)) {
    respond(400, ['ok' => false, 'error' => 'A valid .docx or .pdf filename is required.']);
}

$fileBase64 = (string)($payload[$isPdf ? 'pdf_base64' : 'docx_base64'] ?? '');
if ($fileBase64 === '') {
    respond(400, ['ok' => false, 'error' => ($isPdf ? 'pdf_base64' : 'docx_base64') . ' is required.']);
}

$docxBytes = base64_decode($fileBase64, true);
if ($docxBytes === false) {
    respond(400, ['ok' => false, 'error' => 'Base64 data is not valid.']);
}

$folderSuffix = $isPdf ? '_pdf' : '_docx';
$docxRootDir = $baseDir . DIRECTORY_SEPARATOR . $examName . $folderSuffix;
$docxTargetDir = $subdir === '' ? $docxRootDir : $docxRootDir . DIRECTORY_SEPARATOR . $subdir;

if (!is_dir($docxTargetDir) && !@mkdir($docxTargetDir, 0775, true) && !is_dir($docxTargetDir)) {
    respond(500, ['ok' => false, 'error' => 'Failed to create DOCX target directory.']);
}

$docxPath = build_available_path($docxTargetDir, $filename);
$docxRelativePath = path_to_relative_url($docxPath, $docxRootDir);

if (@file_put_contents($docxPath, $docxBytes) === false) {
    respond(500, ['ok' => false, 'error' => 'Failed to save DOCX file.']);
}

respond(200, [
    'ok' => true,
    'saved_path' => $docxPath,
    'state_path' => $statePath,
    'download_url' => './docx_files.php?action=download&examname=' . rawurlencode($examName) . '&path=' . rawurlencode($docxRelativePath),
]);
