# Magic Impact Tools — Complete Updated Version

This version preserves your current UI and adds scalable configuration.

## Gemini model
The default model is managed in:

`config/models.json`

Current value:

`gemini-flash-latest`

## Questionnaire languages
Languages are managed in:

`config/languages.json`

Add or remove language names there without editing `app.py`.

## AI system prompt
The Gemini questionnaire instruction is managed in:

`config/system_prompt.txt`

You can improve the AI prompt without editing `app.py`.

## Local Gemini key
Copy:

`.streamlit/secrets.toml.example`

to:

`.streamlit/secrets.toml`

Then add your real key. The real secrets file is intentionally excluded from this ZIP and from GitHub.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```


## Multilingual XLSForm fix
The exporter now creates standard XLSForm columns such as `label::English (en)` and `label::Hindi (hi)`, including translated choice labels and constraint messages.
