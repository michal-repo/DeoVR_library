<?php

// Config
$ip="192.168.1.2";
$use_login_and_pass = false;
$superSecretLogin = "user";
$superSecretPassword = "secret";

if ($_COOKIE['PHPSESSID']) {
    session_id($_COOKIE['PHPSESSID']);
}
session_start(); 
$now = time();
if (isset($_SESSION['discard_after']) && $now > $_SESSION['discard_after']) {
    session_unset();
    session_destroy();
    session_start();
}
$_SESSION['discard_after'] = $now + 3600;

$accessDeniedJson = '{"scenes": [{"name": "LOG IN","list": [{"title": "LOGIN","thumbnailUrl": "http://' . $ip . '/deovr/empty.png","encodings": [{"name": "h264", "videoSources": [{"resolution": 1440, "url": "http://' . $ip . '/deovr/fake.mp4"}]}]},{"title": "LOGIN","thumbnailUrl": "http://' . $ip . '/deovr/empty.png","encodings": [{"name": "h264", "videoSources": [{"resolution": 1440, "url": "http://' . $ip . '/deovr/fake.mp4"}]}]},{"title": "LOGIN","thumbnailUrl": "http://' . $ip . '/deovr/empty.png","encodings": [{"name": "h264", "videoSources": [{"resolution": 1440, "url": "http://' . $ip . '/deovr/fake.mp4"}]}]}]}]}';

if(isset($_POST["login"]) && isset($_POST["password"])){
    if($_POST["login"] == $superSecretLogin && $_POST["password"] == $superSecretPassword){
        $_SESSION["authorized"] = true;
    } else {
        $_SESSION["authorized"] = false;
    }
}

if(!$_SESSION["authorized"] && $use_login_and_pass){
    header('Content-Type: application/json; charset=utf-8');
    echo $accessDeniedJson;
} else {
    $data = file_get_contents("deovr.json");
    $data = json_decode($data);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($data);
}
