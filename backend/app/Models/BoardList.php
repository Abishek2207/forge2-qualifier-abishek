<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

/**
 * Backend for the Forge 2 Kanban application
 */
class BoardList extends Model
{
    use HasFactory;

    protected $table = 'lists'; // Overriding default table name to match migration

    protected $fillable = [
        'board_id',
        'title',
        'position',
    ];

    public function board()
    {
        return $this->belongsTo(Board::class);
    }

    public function cards()
    {
        return $this->hasMany(Card::class, 'list_id');
    }
}
