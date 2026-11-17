# Helixis Solar Yield Maps – partnerapp

Inloggningsskyddad Streamlit-app med Helixis-profil. Efter inloggning kommer partnern till en startsida med ett kort per land. Varje kort öppnar en interaktiv karta med uppskattad årlig värmeproduktion för LC10 HW och LC20 HW.

Har en användare bara tillgång till ett land hoppar appen över startsidan och visar kartan direkt.

## Filer

| Fil | Vad den gör |
|---|---|
| `app.py` | Inloggning, startsida, kartsidor och listan över länder (`COUNTRIES`) |
| `maps/italy.html`, `maps/rwanda.html` | Kartorna, med all DNI-data från Global Solar Atlas inbakad |
| `assets/outlines/` | Landkonturer till korten på startsidan |
| `assets/` | Helixis logga (mörk, vit) och den blå symbolen |
| `.streamlit/config.toml` | Helixis färger enligt stilguiden (#1444E2, #1A252C, #DFDADC) |
| `requirements.txt` | Paket som Streamlit Cloud installerar |
| `secrets.toml.example` | Mall för användare, lösenord och vem som ser vilket land |
| `.gitignore` | Hindrar att lösenordsfilen laddas upp till GitHub |

## Användare och åtkomst

Allt styrs i appens **Secrets** på Streamlit Cloud (Settings → Secrets):

```toml
[passwords]
admin = "ett-långt-eget-lösenord"
partner_italia = "ett-annat-lösenord"
partner_rwanda = "ett-tredje-lösenord"

[access]
admin = ["*"]                 # ser alla länder
partner_italia = ["italy"]    # ser bara Italien
partner_rwanda = ["rwanda"]   # ser bara Rwanda
```

- `["*"]` betyder alla länder, även länder som läggs till senare.
- En användare som saknas under `[access]` ser inga kartor.
- Tar du bort hela `[access]`-avsnittet ser alla användare alla länder.
- Ändringar i Secrets gäller direkt, utan ny uppladdning.

## Lägga till ett land

Be Claude göra en karta för landet. Det som behövs är:

1. en kartfil i `maps/`, till exempel `maps/kenya.html`
2. en kontur i `assets/outlines/`, till exempel `assets/outlines/kenya.svg`
3. ett nytt block i listan `COUNTRIES` i `app.py`
4. landets nyckel (`kenya`) under `[access]` för de användare som ska se det

## Publicera på Streamlit Cloud

1. Ladda upp hela mappen till ett GitHub-repo, inklusive `.streamlit`, `assets` och `maps`.
2. På share.streamlit.io: **Create app**, välj repot, branch `main` och main file `app.py`.
3. Klistra in användarna under **Advanced settings → Secrets** och klicka på **Deploy**.
4. Gå till appens **Settings → Sharing** och gör den publik. Inloggningen i appen skyddar ändå innehållet.

## Säkerhet

- Utan lösenord i Secrets släpps ingen in. Det finns inget demoläge.
- Efter 5 fel i rad låses inloggningen i 60 sekunder.
- Ge varje kund ett eget användarnamn, så kan du stänga av en kund utan att påverka andra.
