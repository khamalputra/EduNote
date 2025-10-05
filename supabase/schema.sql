-- Schema definition for EduNote
create extension if not exists "pgcrypto";

create table if not exists public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    full_name text,
    avatar_url text,
    created_at timestamp with time zone default timezone('utc', now())
);

create table if not exists public.notes (
    id uuid primary key default gen_random_uuid(),
    owner uuid not null references auth.users(id) on delete cascade,
    title text not null,
    body_markdown text,
    tags text[] default array[]::text[],
    created_at timestamp with time zone default timezone('utc', now()),
    updated_at timestamp with time zone default timezone('utc', now())
);

create table if not exists public.decks (
    id uuid primary key default gen_random_uuid(),
    owner uuid not null references auth.users(id) on delete cascade,
    name text not null,
    description text,
    created_at timestamp with time zone default timezone('utc', now()),
    updated_at timestamp with time zone default timezone('utc', now())
);

create table if not exists public.cards (
    id uuid primary key default gen_random_uuid(),
    deck_id uuid not null references public.decks(id) on delete cascade,
    owner uuid not null references auth.users(id) on delete cascade,
    front text not null,
    back text not null,
    note_id uuid references public.notes(id) on delete set null,
    ease real default 2.5,
    interval_days integer default 0,
    reps integer default 0,
    lapses integer default 0,
    due_at date default (timezone('utc', now()))::date,
    suspended boolean default false,
    created_at timestamp with time zone default timezone('utc', now()),
    updated_at timestamp with time zone default timezone('utc', now())
);

create table if not exists public.reviews (
    id uuid primary key default gen_random_uuid(),
    card_id uuid not null references public.cards(id) on delete cascade,
    owner uuid not null references auth.users(id) on delete cascade,
    grade integer not null check (grade between 0 and 5),
    reviewed_at timestamp with time zone default timezone('utc', now()),
    prev_interval integer,
    new_interval integer,
    prev_ease real,
    new_ease real
);

create index if not exists notes_owner_idx on public.notes(owner);
create index if not exists decks_owner_idx on public.decks(owner);
create index if not exists cards_owner_due_idx on public.cards(owner, due_at);
create index if not exists reviews_owner_reviewed_idx on public.reviews(owner, reviewed_at desc);

create or replace function public.touch_updated_at()
returns trigger as $$
begin
    new.updated_at = timezone('utc', now());
    return new;
end;
$$ language plpgsql;

create trigger notes_touch_updated_at
before update on public.notes
for each row execute function public.touch_updated_at();

create trigger decks_touch_updated_at
before update on public.decks
for each row execute function public.touch_updated_at();

create trigger cards_touch_updated_at
before update on public.cards
for each row execute function public.touch_updated_at();
