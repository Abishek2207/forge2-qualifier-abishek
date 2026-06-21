# Forge 2 Kanban Backend

Laravel API scaffold for Forge 2 Kanban
SQLite-ready backend

## Directory Structure
- `app/Models/`: Eloquent models defining relationships
- `database/migrations/`: Database schema definitions
- `routes/api.php`: REST API endpoints

## Endpoints
- `GET /api/health` - Check backend status
- `GET /api/boards` - Fetch Kanban boards

## Local run instructions:
```bash
composer install
cp .env.example .env
php artisan key:generate
php artisan migrate
php artisan serve
```