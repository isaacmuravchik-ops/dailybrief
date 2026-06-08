create table if not exists reminders (
    id          bigint generated always as identity primary key,
    text        text not null,
    due_date    date not null,
    recurring   text,            -- null | 'daily' | 'weekly' | 'monthly'
    sent        boolean default false,
    created_at  timestamptz default now()
);

alter table reminders enable row level security;
-- No public policies: only the service-role key (used server-side) can access.
