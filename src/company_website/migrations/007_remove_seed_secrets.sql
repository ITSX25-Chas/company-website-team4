-- Tar bort testdata och hemligheter som 002 och 004 lade in (F22). De filerna
-- ändras inte, eftersom de redan är körda i klustret. Den här migreringen
-- städar både befintliga och nya databaser.

-- Testkontot flag hade sitt lösenord i klartext i kolumnen för hashen.
DELETE FROM users WHERE username = 'flag';

-- Anteckningar med inloggningsuppgifter eller flaggor.
UPDATE users SET internal_notes = NULL
WHERE internal_notes LIKE '%staging123%' OR internal_notes LIKE '%ITSX25{%';
