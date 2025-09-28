-- Add restrictions column if it doesn't exist
ALTER TABLE public.guests ADD COLUMN IF NOT EXISTS restrictions text;

-- Consolidate ideas columns (stag_ideas -> ideas if ideas is null or empty)
UPDATE public.guests 
SET ideas = COALESCE(NULLIF(TRIM(stag_ideas), ''), NULLIF(TRIM(ideas), ''))
WHERE (ideas IS NULL OR TRIM(ideas) = '') AND stag_ideas IS NOT NULL AND TRIM(stag_ideas) != '';

UPDATE public.guests 
SET ideas = COALESCE(NULLIF(TRIM(hen_ideas), ''), NULLIF(TRIM(ideas), ''))
WHERE (ideas IS NULL OR TRIM(ideas) = '') AND hen_ideas IS NOT NULL AND TRIM(hen_ideas) != '';

-- Consolidate friday room columns (take the higher value)
UPDATE public.guests 
SET friday_room = GREATEST(COALESCE(friday_room, -2), COALESCE(friday_stay_preference, -2))
WHERE friday_stay_preference IS NOT NULL;

-- Consolidate saturday room columns (take the higher value)
UPDATE public.guests 
SET saturday_room = GREATEST(COALESCE(saturday_room, -2), COALESCE(saturday_stay_preference, -2))
WHERE saturday_stay_preference IS NOT NULL;

-- Drop the duplicate columns
ALTER TABLE public.guests DROP COLUMN IF EXISTS stag_ideas;
ALTER TABLE public.guests DROP COLUMN IF EXISTS hen_ideas;
ALTER TABLE public.guests DROP COLUMN IF EXISTS friday_stay_preference;
ALTER TABLE public.guests DROP COLUMN IF EXISTS saturday_stay_preference;