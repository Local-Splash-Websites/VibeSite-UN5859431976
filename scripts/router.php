<?php
// Router for `php -S` so local preview matches the .htaccess clean URLs.
$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$root = __DIR__ . '/../public';
if ($path !== '/' && is_file($root . $path)) return false;
if ($path === '/') { readfile("$root/index.html"); return true; }
$file = $root . rtrim($path, '/') . '.html';
if (is_file($file)) { readfile($file); return true; }
http_response_code(404); readfile("$root/404.html"); return true;
