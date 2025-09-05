CREATE TABLE tasks(
                id text primary key,
                course text,
                title text not null,
                status text check(status in ('todo','doing','review','done','blocked')) not null,
                due_at text,
                est_minutes integer,
                weight real default 1.0,
                category text,
                anchor integer default 0,
                notes text,
                created_at text not null,
                updated_at text not null
            , checklist text, parent_id text);
CREATE TABLE deps(
                task_id text not null,
                blocks_id text not null,
                primary key(task_id, blocks_id)
            );
CREATE TABLE events(
                id integer primary key autoincrement,
                at text not null,
                task_id text not null,
                field text not null,
                from_val text,
                to_val text
            );
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE scores(
                task_id text primary key,
                score real not null,
                factors text not null, -- JSON string
                computed_at text not null
            );
CREATE TABLE now_queue(
                pos integer primary key,
                task_id text not null
            );
CREATE VIRTUAL TABLE tasks_fts using fts5(
                title, notes, content='tasks', content_rowid='rowid'
            );
CREATE TABLE IF NOT EXISTS 'tasks_fts_data'(id INTEGER PRIMARY KEY, block BLOB);
CREATE TABLE IF NOT EXISTS 'tasks_fts_idx'(segid, term, pgno, PRIMARY KEY(segid, term)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS 'tasks_fts_docsize'(id INTEGER PRIMARY KEY, sz BLOB);
CREATE TABLE IF NOT EXISTS 'tasks_fts_config'(k PRIMARY KEY, v) WITHOUT ROWID;
CREATE INDEX idx_tasks_status on tasks(status);
CREATE INDEX idx_tasks_course on tasks(course);
CREATE INDEX idx_tasks_due on tasks(due_at);
CREATE INDEX idx_deps_task on deps(task_id);
CREATE INDEX idx_deps_blocks on deps(blocks_id);
