<?php

namespace App\Http\Controllers;

use Illuminate\Http\Client\ConnectionException;
use Illuminate\Support\Facades\Http;

class ConnectionController extends Controller
{
    // handle button clicks from the remote control
    public function webRemote($_command)
    {
        // try to send command to motor via a cloudflare tunnel
        try {
            $response = Http::withBody($_command)->post("devices.zayndev.org");
        } catch (ConnectionException $e) {
            return $e->getMessage();
        }

        // let the caller know how the request wen
        return "{$response->body()} ::: {$response->reason()}";
    }
}
