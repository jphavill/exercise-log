# iPhone Shortcut Setup (NFC)

Use one NFC automation per exercise. Each automation should call `POST https://<tailnet-host>/api/logs` with JSON and `Content-Type: application/json`.

## L-sit
- Menu: 10 sec, 15 sec, 20 sec, 30 sec, Custom
- If Custom: ask for number input (seconds)
- POST body:

```json
{
  "exercise_slug": "l-sit",
  "duration_seconds": 20
}
```

## Pull-ups
- Menu: 1, 3, 5, Custom
- If Custom: ask for reps
- POST body:

```json
{
  "exercise_slug": "pullups",
  "reps": 5
}
```

## Weighted Pull-ups
- Menu: 1 rep @ last weight, 3 reps @ last weight, Custom reps, Custom weight, Custom both
- Use `Get Variable` / `Set Variable` in Shortcuts to persist last used weight locally
- POST body:

```json
{
  "exercise_slug": "weighted-pullups",
  "reps": 3,
  "weight_lbs": 25
}
```

## Mace Swings
- Menu: 10, 20, 30, Custom
- If Custom: ask for reps
- POST body:

```json
{
  "exercise_slug": "mace-swings",
  "reps": 20
}
```

## Result Message
After `Get Contents of URL`, show notification/alert using response fields:
- logged value
- `today_total`
- `last_7_days_total`
