-- Spaced repetition scheduling RPC
create or replace function public.apply_review(p_card uuid, p_grade int)
returns public.cards
language plpgsql
security definer
set search_path = public
as $$
declare
    v_card public.cards;
    v_today date := timezone('utc', now())::date;
    v_new_interval integer;
    v_new_ease real;
    v_new_reps integer;
    v_new_lapses integer;
    v_prev_interval integer;
    v_prev_ease real;
begin
    if p_grade < 0 or p_grade > 5 then
        raise exception 'Grade must be between 0 and 5';
    end if;

    select * into v_card
    from public.cards
    where id = p_card and owner = auth.uid()
    for update;

    if not found then
        raise exception 'Card not found or access denied';
    end if;

    v_prev_interval := coalesce(v_card.interval_days, 0);
    v_prev_ease := coalesce(v_card.ease, 2.5);

    v_new_reps := v_card.reps + 1;
    v_new_lapses := v_card.lapses;
    v_new_ease := v_prev_ease;

    if p_grade < 3 then
        v_new_ease := greatest(1.3, v_prev_ease - 0.2);
        v_new_interval := 1;
        v_new_lapses := v_card.lapses + 1;
    else
        v_new_ease := greatest(1.3, v_prev_ease + (0.1 - (5 - p_grade) * (0.08 + (5 - p_grade) * 0.02)));
        if v_card.reps = 0 then
            v_new_interval := 1;
        elsif v_card.reps = 1 then
            v_new_interval := 6;
        else
            v_new_interval := greatest(1, round(v_prev_interval * v_new_ease))::int;
        end if;
    end if;

    update public.cards
    set
        interval_days = v_new_interval,
        ease = v_new_ease,
        reps = v_new_reps,
        lapses = v_new_lapses,
        due_at = v_today + v_new_interval,
        updated_at = timezone('utc', now())
    where id = v_card.id
    returning * into v_card;

    insert into public.reviews (
        card_id,
        owner,
        grade,
        reviewed_at,
        prev_interval,
        new_interval,
        prev_ease,
        new_ease
    ) values (
        v_card.id,
        v_card.owner,
        p_grade,
        timezone('utc', now()),
        v_prev_interval,
        v_new_interval,
        v_prev_ease,
        v_new_ease
    );

    return v_card;
end;
$$;
