-- Enable row level security
alter table public.profiles enable row level security;
alter table public.notes enable row level security;
alter table public.decks enable row level security;
alter table public.cards enable row level security;
alter table public.reviews enable row level security;

-- Profiles policies
create policy "Profiles are self readable" on public.profiles
for select using (id = auth.uid());

create policy "Profiles are self updatable" on public.profiles
for update using (id = auth.uid()) with check (id = auth.uid());

create policy "Profiles can insert self" on public.profiles
for insert with check (id = auth.uid());

-- Generic CRUD policies for notes, decks, cards, reviews
create policy "Notes accessible to owner" on public.notes
for all using (owner = auth.uid()) with check (owner = auth.uid());

create policy "Decks accessible to owner" on public.decks
for all using (owner = auth.uid()) with check (owner = auth.uid());

create policy "Cards accessible to owner" on public.cards
for all using (owner = auth.uid()) with check (owner = auth.uid());

create policy "Reviews accessible to owner" on public.reviews
for all using (owner = auth.uid()) with check (owner = auth.uid());
