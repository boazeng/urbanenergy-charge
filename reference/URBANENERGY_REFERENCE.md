# Urban Energy (Evoltsoft) — Reverse-Engineered Reference

מקור: ניתוח HAR של `urbanenergy.web.app/dashboards/analytics` (24/06/2026).
מטרה: ללמוד מה המערכת הקיימת עושה, כדי לבנות מקבילה עצמאית (CSMS + דשבורד ניהול).

## הספק האמיתי
- המערכת היא **white-label של Evoltsoft** (ספק EV-charging SaaS הודי).
- ראיות: `system@evoltsoft.com` בשדות `updated_by_user_email`; backend ב-`asia-south1`.
- "Urban Energy - Yael Israel Group" = ה-Business Organisation שלך אצל Evoltsoft.
- **משמעות:** ייתכן ש-Evoltsoft חושפת REST/OCPI לחיוב — מסלול מהיר יותר מאשר בנייה מאפס. כדאי לבדוק מולם.

## Stack
- Frontend: Vuexy (Vue) SPA על Firebase Hosting.
- Backend: Firebase **Cloud Functions** — `https://asia-south1-urbanenergy-prod.cloudfunctions.net`.
- DB: **Firestore** (שאילתות בפורמט `{conditions:[{key,clause,value,isDate}], limit, offset, orderByField, direction}`).
- Auth: Firebase Auth (`identitytoolkit.googleapis.com`).

## היררכיית הישויות
```
Business Organisation
  └─ Partner Organisation (×17)   — לקוח עם ארנק + total_unsettled_amount (סילוק)
       └─ Location (×18)
            └─ Charging Station (×122)
                 └─ EVSE          — סטטוסים: AVAILABLE/CHARGING/PREPARING/FINISHING/UNKNOWN
                      └─ Session (×15,738)  — Finished/Running/Rejected
EV Drivers (×221)  ·  Wallet + Topups (×803)  ·  Revenue/Transactions
```

### Partner Organisation — שדות (מהתשובה האמיתית)
`id, name, status(ACTIVE), party_id(URE), type(PARTNER), country_code(IL),
address{address,landmark,zip_code,city,state,country}, billing, payments,
settlementInfo, idling_fee, subscription(bool), business_organisation_id,
business_organisation_name, wallet{total_unsettled_amount, updated_at},
created_at, updated_at, created_by_user_email, updated_by_user_email`

## מודל עסקי: ארנק נטען מראש (Prepaid Wallet)
- נהגים מבצעים **topup** לארנק; טעינה מנכה מהיתרה.
- לכל Partner יש `total_unsettled_amount` → הסכום לסילוק מול ה-ERP (**Priority**).
- החיוב אינו "חשבונית פר-טעינה" קלאסי אלא **סילוק תקופתי** של יתרות לא-מסולקות.

## API של מסך Analytics (Cloud Functions)
כל הקריאות `POST` (אלא אם צוין), גוף הבקשה לרוב `{condition:[...]}` או `{filter:"<from> to <to>"}`.

| Endpoint | מחזיר | דוגמה |
|---|---|---|
| `/portal/partner/organisation/list/all` | רשימת Partners (אובייקטים מלאים) | 17 |
| `/analytics/dashboard/location/count` | מס' אתרים | 18 |
| `/analytics/dashboard/chargingStation/count` | מס' עמדות | 122 |
| `/analytics/dashboard/partnerOrganisation/count` | מס' שותפים | 17 |
| `/analytics/dashboard/user/count` | מס' משתמשי פורטל | 8 |
| `/analytics/dashboard/evDrivers/count` | מס' נהגים | 221 |
| `/analytics/dashboard/totalEnergy/consumption` | kWh מצטבר | 327,952.6 |
| `/analytics/dashboard/totalTransactions/charging` | סכום עסקאות טעינה | 239,002.3 |
| `/analytics/dashboard/remainingWallet/balance` | יתרת ארנקים | 202,928.8 |
| `/analytics/dashboard/topup/count` | מס' טעינות ארנק | 803 |
| `/analytics/dashboard/revenue` (PUT) | סדרת הכנסות יומית | 390 ימים |
| `/analytics/dashboard` | אגרגציות יומיות: abs_uptime, abs_charge_time, abs_idle_time, failedSessions, totalSessions, totalCharger, דליי-זמינות, revenue{transaction_amount,transaction_count} | |
| `/analytics/dashboard/session/logs` | פילוח סשנים | {Running:5, Rejected:34, Finished:15738} |
| `/analytics/dashboard/evse/logs` | פילוח סטטוס EVSE | {AVAILABLE:82, CHARGING:5, UNKNOWN:17, PREPARING:11, FINISHING:7} |
| `/analytics/dashboard/consumption/summary` | kWh ליום (טווח) | [{date,totalKwh}] |

## מפת מסכים מומלצת לדשבורד שלנו (React/TACT RTL)
1. **Analytics** — כרטיסי KPI (אתרים/עמדות/שותפים/נהגים/אנרגיה/עסקאות/ארנקים) + גרף הכנסות + צריכה יומית + פילוח סטטוס עמדות + אמינות.
2. **שותפים (Partners)** — רשימה, ארנק, חוב לסילוק, כתובת.
3. **אתרים (Locations)**.
4. **עמדות (Chargers/EVSE)** — סטטוס חי, שליטה (start/stop/reset).
5. **טעינות (Sessions)** — היסטוריה, kWh, נהג, עלות.
6. **נהגים (EV Drivers)** + **ארנקים/Topups**.
7. **חיוב/סילוק → Priority**.

## מסקנות לבנייה
- מודל ה-DB שלנו צריך להוסיף: Partner/Org, Location, Driver, Wallet, Topup, Transaction, Settlement — מעבר ל-EVSE/Session שכבר יש.
- חיבור Priority = **סילוק `total_unsettled_amount` פר-Partner**, לא רק חשבונית פר-טעינה.
- לבדוק מול Evoltsoft אם יש API/OCPI (מסלול מהיר לחיוב במקביל לבניית ה-CSMS).
