<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="initial-scale=1, width=device-width"/>
    <meta http-equiv="X-UA-Compatible" content="ie=edge">

    <title>"ROLLIN" IoT controls</title>

    <!-- Poppins font -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link
        href="https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&display=swap"
        rel="stylesheet"
    >
    <!-- Nunito Sans font -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link
        href="https://fonts.googleapis.com/css2?family=Nunito+Sans:ital,opsz,wght@0,6..12,200..1000;1,6..12,200..1000&display=swap"
        rel="stylesheet"
    >

    <!-- use Nunito Sans font -->
    <style>
        .nunito-sans {
            font-family: "Nunito Sans", sans-serif;
            font-optical-sizing: auto;
            font-style: normal;
            font-variation-settings: "wdth" 100,
            "YTLC" 500;
        }
    </style>

    <!-- use import style sheet -->
    @viteReactRefresh
    @vite('resources/sass/app.scss')
</head>
<body style="
    background-color: #8BC6EC;
    background-image: linear-gradient(135deg, #8BC6EC 0%, #9599E2 100%);
    font-family: 'Poppins', sans-serif;
    background-repeat: no-repeat;
    min-height: 100vh;
">

<!-- ROLLLIN React app will mount to this DOM element -->
<div id="root"/>

<!-- import react app -->
@vite('resources/tsx/Main.tsx')
</body>
</html>
