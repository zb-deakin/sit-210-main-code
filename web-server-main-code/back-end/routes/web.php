<?php

use App\Http\Controllers\ConnectionController;
use Illuminate\Support\Facades\Route;

Route::get('/', function () {
    return view('interface');
});


Route::post('/connection/{blindId}', [ConnectionController::class, 'create']);
