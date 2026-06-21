<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;

// Backend for the Forge 2 Kanban application

Route::get('/health', function () {
    return response()->json([
        'status' => 'success',
        'message' => 'Forge 2 Kanban Backend API is running.',
        'timestamp' => now()->toIso8601String(),
    ]);
});

Route::get('/boards', function () {
    // Scaffold implementation for retrieving boards
    // In a real application, this would call a controller (e.g., BoardController@index)
    return response()->json([
        'data' => [
            [
                'id' => 1,
                'title' => 'Forge 2 Qualifier',
                'description' => 'Kanban board for the qualifier tasks.',
            ]
        ]
    ]);
});
