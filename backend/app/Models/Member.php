<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

/**
 * Backend for the Forge 2 Kanban application
 */
class Member extends Model
{
    use HasFactory;

    protected $fillable = [
        'name',
        'email',
        'avatar_url',
    ];

    public function cards()
    {
        return $this->belongsToMany(Card::class);
    }
}
