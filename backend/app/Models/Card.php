<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

/**
 * Backend for the Forge 2 Kanban application
 */
class Card extends Model
{
    use HasFactory;

    protected $fillable = [
        'list_id',
        'title',
        'description',
        'due_date',
        'position',
    ];

    public function list()
    {
        return $this->belongsTo(BoardList::class, 'list_id');
    }

    public function tags()
    {
        return $this->belongsToMany(Tag::class);
    }

    public function members()
    {
        return $this->belongsToMany(Member::class);
    }
}
